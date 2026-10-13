# Etsy to Facebook

Posts one Etsy listing a day to the Lemoine Facebook Page: the product photo, a short caption and the Etsy link. It uses the same Etsy pull as the Pinterest pipeline.

- `post_facebook.py` picks the next listing and posts it. Never-posted listings go first, best-viewed first. When all of them have gone out, it starts round again with a fresh caption.
- `captions.py` holds the caption variants by category.
- `captions.json` (optional, yours to write) holds your own words for a listing, keyed by listing id. It always beats the templates. A string or a list of strings works:

  ```json
  { "1234567890": "[what this piece is really about, in your words]" }
  ```

- `get_page_token.py` is the one-time setup on your laptop.
- `.github/workflows/facebook-post.yml` is the daily job.

## Setup on your laptop (about 20 minutes)

1. **Create the Meta app.** Go to developers.facebook.com/apps, then Create app. Pick the use case for managing everything on your Page. Name it something like `lemoine-posts`.
2. **Fill in App settings > Basic.** Set the privacy policy URL to `https://www.johnnylemoine.com/privacy` and pick a category. Copy the App ID and App Secret.
   Your privacy page already has a Pinterest section. Add a matching line for Facebook, for example: *This site uses a Facebook integration ("lemoine-posts") to publish my own Etsy artwork to my own Facebook Page.*
3. **Get a user token.** Open the Graph API Explorer (developers.facebook.com/tools/explorer) and select your app. Add the permissions `pages_show_list`, `pages_manage_posts` and `pages_read_engagement`, then click Generate Access Token. In the login dialog, tick the Lemoine Page. Copy the token.
4. **Run the setup script** from this repo:

   ```
   python3 facebook/get_page_token.py
   ```

   Paste the App ID, App Secret and token when it asks (nothing shows as you type). It saves `FB_PAGE_ID` and `FB_PAGE_TOKEN` to GitHub if the `gh` CLI is logged in. If not, it tells you where to add them by hand.
5. **Switch the app to Live** with the toggle at the top of the app dashboard. While it's in Development mode, posts show to you and nobody else, and photo posts can appear without the photo.
6. **Preview, then test.** On GitHub, go to Actions > Daily Facebook post > Run workflow, and leave "Preview only" ticked. The log shows the next 7 posts. When the captions look right, run it again unticked. One listing posts.
7. **Check it from a logged-out browser** (a private window). Then uncomment the `schedule` block in the workflow, and it posts every day at 10am Pacific.

## If something breaks

- **Error code 190:** the Page token was revoked, usually after a Facebook password change. Run step 3 and 4 again.
- **Permission error on a Live app:** Meta may want an App Review for `pages_manage_posts`. Posting to a Page you admin, from an app you admin, normally doesn't need one. If it does, the error says so.
