// scripts/strip_js_safe.js
const fs = require("fs");
const path = require("path");

const SRC = "frontend/src";
const DST = "front";

// Funkcja do usuwania komentarzy z kodu
function stripComments(code) {
  return code
    // usuwa komentarze liniowe //
    .replace(/\/\/.*$/gm, "")
    // usuwa komentarze blokowe /* */
    .replace(/\/\*[\s\S]*?\*\//g, "")
    // usuwa JSX komentarze {/* */}
    .replace(/\{\/\*[\s\S]*?\*\/\}/g, "");
}

// Rekurencyjne przetwarzanie folderu
function walk(dir) {
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    if (fs.statSync(full).isDirectory()) {
      walk(full);
    } else if (/\.(js|jsx|ts|tsx)$/.test(full)) {
      const code = fs.readFileSync(full, "utf8");
      const stripped = stripComments(code);

      const outPath = path.join(DST, path.relative(SRC, full));
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, stripped, "utf8");
    }
  }
}

// Czyścimy folder docelowy
fs.rmSync(DST, { recursive: true, force: true });
walk(SRC);

console.log(`✅ Wszystkie pliki JS/TS/JSX/TSX zostały przetworzone do ${DST}`);
