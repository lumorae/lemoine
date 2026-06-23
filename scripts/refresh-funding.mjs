#!/usr/bin/env node
// Weekly funding refresh for the Lemoine "Leads" Airtable base.
//
// For every lead in the "2026 Leads" table this script asks Claude (with the
// web search tool) for the company's latest fundraising stage, then writes the
// result back into the "Funding Stage" and "Funding Detail" columns.
//
// It is intentionally dependency-free: it talks to the Airtable REST API and
// the Anthropic Messages API directly using the built-in fetch (Node 18+).
//
// Required environment variables:
//   AIRTABLE_TOKEN     Airtable personal access token (scopes: data.records:read/write)
//   ANTHROPIC_API_KEY  Anthropic API key (used for funding research w/ web search)
// Optional:
//   FUNDING_MODEL      Anthropic model id (default: claude-sonnet-4-6)
//   DRY_RUN=1          Research + log, but do NOT write back to Airtable
//   ONLY_EMPTY=1       Only refresh rows whose Funding Stage is currently empty

const BASE_ID = "appZpCWT67dprKW83";
const TABLE_ID = "tbliWGk0iWgfhUGPj"; // "2026 Leads"

const FIELD = {
  company: "fld49ltt7bXHUmPqx",
  industry: "fld4yCVgvY930jMGL",
  website: "fldE1qiQ4aXRb9dUk",
  fundingStage: "fldKbkGyS1uHZHGB5",
  fundingDetail: "fldz8YrnKrylWlYQz",
};

// Must match the singleSelect options on the "Funding Stage" field exactly.
const STAGES = [
  "Bootstrapped",
  "Pre-seed",
  "Seed",
  "Series A",
  "Series B+",
  "Acquired/Public",
  "Unknown",
];

const AIRTABLE_TOKEN = requireEnv("AIRTABLE_TOKEN");
const ANTHROPIC_API_KEY = requireEnv("ANTHROPIC_API_KEY");
const MODEL = process.env.FUNDING_MODEL || "claude-sonnet-4-6";
const DRY_RUN = process.env.DRY_RUN === "1";
const ONLY_EMPTY = process.env.ONLY_EMPTY === "1";

function requireEnv(name) {
  const v = process.env[name];
  if (!v) {
    console.error(`Missing required env var: ${name}`);
    process.exit(1);
  }
  return v;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---- Airtable -------------------------------------------------------------

async function fetchAllRecords() {
  const records = [];
  let offset;
  do {
    const url = new URL(
      `https://api.airtable.com/v0/${BASE_ID}/${TABLE_ID}`
    );
    url.searchParams.set("pageSize", "100");
    url.searchParams.set("returnFieldsByFieldId", "true");
    if (offset) url.searchParams.set("offset", offset);

    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${AIRTABLE_TOKEN}` },
    });
    if (!res.ok) throw new Error(`Airtable read ${res.status}: ${await res.text()}`);
    const data = await res.json();
    records.push(...data.records);
    offset = data.offset;
  } while (offset);
  return records;
}

async function patchRecords(updates) {
  // Airtable allows max 10 records per write request.
  for (let i = 0; i < updates.length; i += 10) {
    const batch = updates.slice(i, i + 10);
    const res = await fetch(
      `https://api.airtable.com/v0/${BASE_ID}/${TABLE_ID}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${AIRTABLE_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ records: batch, returnFieldsByFieldId: true }),
      }
    );
    if (!res.ok) throw new Error(`Airtable write ${res.status}: ${await res.text()}`);
    await sleep(250); // stay under ~5 req/sec
  }
}

// ---- Funding research (Claude + web search) -------------------------------

async function researchFunding(company, website, industry) {
  const prompt = [
    `Find the most recent known fundraising / funding stage for this company.`,
    `Company: ${company}`,
    website ? `Website: ${website}` : null,
    industry ? `Industry: ${industry}` : null,
    ``,
    `Choose exactly one "stage" from this list: ${STAGES.join(", ")}.`,
    `- If it raised multiple rounds, use the latest (Series B or beyond = "Series B+").`,
    `- If it is an individual, a VC firm, an incubator/accelerator, or a non-profit`,
    `  (i.e. not a fundraising target), use stage "Unknown" and say so in the detail.`,
    `- If you cannot find reliable info, use "Unknown".`,
    ``,
    `Respond with ONLY a JSON object, no prose, no code fences:`,
    `{"stage": "<one of the list>", "detail": "<max 12 words: amount/year/lead investor, or what it is>"}`,
  ]
    .filter(Boolean)
    .join("\n");

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 400,
      tools: [{ type: "web_search_20250305", name: "web_search", max_uses: 4 }],
      messages: [{ role: "user", content: prompt }],
    }),
  });
  if (!res.ok) throw new Error(`Anthropic ${res.status}: ${await res.text()}`);
  const data = await res.json();

  // The final text block holds the JSON answer.
  const text = (data.content || [])
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("")
    .trim();

  const match = text.match(/\{[\s\S]*\}/);
  if (!match) throw new Error(`No JSON in model reply: ${text.slice(0, 200)}`);
  const parsed = JSON.parse(match[0]);
  const stage = STAGES.includes(parsed.stage) ? parsed.stage : "Unknown";
  const detail = String(parsed.detail || "").slice(0, 100);
  return { stage, detail };
}

// ---- Main -----------------------------------------------------------------

async function main() {
  console.log(`Funding refresh starting (model=${MODEL}, dryRun=${DRY_RUN}, onlyEmpty=${ONLY_EMPTY})`);
  const records = await fetchAllRecords();
  console.log(`Fetched ${records.length} leads.`);

  const updates = [];
  for (const rec of records) {
    const f = rec.fields || {};
    const company = f[FIELD.company];
    if (!company) continue;
    if (ONLY_EMPTY && f[FIELD.fundingStage]) continue;

    const website = f[FIELD.website];
    const industry = f[FIELD.industry]?.name; // single select -> {name}

    try {
      const { stage, detail } = await researchFunding(company, website, industry);
      console.log(`  ${company} -> ${stage} :: ${detail}`);
      updates.push({
        id: rec.id,
        fields: { [FIELD.fundingStage]: stage, [FIELD.fundingDetail]: detail },
      });
    } catch (err) {
      console.error(`  ${company} -> FAILED: ${err.message}`);
    }
    await sleep(500); // gentle pacing between research calls
  }

  if (DRY_RUN) {
    console.log(`DRY_RUN: would update ${updates.length} records.`);
    return;
  }
  await patchRecords(updates);
  console.log(`Updated ${updates.length} records.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
