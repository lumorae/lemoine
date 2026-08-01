// Stage the animation for offline capture: vendor three.js from node_modules
// and rewrite the CDN import in the site script to the local copy.
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);

fs.mkdirSync(path.join(DIR, 'out'), { recursive: true });

fs.copyFileSync(
  path.join(DIR, 'node_modules/three/build/three.module.js'),
  path.join(DIR, 'three.module.js')
);

const src = fs.readFileSync(path.join(DIR, '../lemoine-explosion-github.js'), 'utf8');
fs.writeFileSync(
  path.join(DIR, 'lemoine-explosion.local.js'),
  src.replace(
    'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
    './three.module.js'
  )
);

console.log('assets staged');
