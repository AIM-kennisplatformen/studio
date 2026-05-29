import path from "path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import https from "https";
import { execSync } from "child_process";
import { createWriteStream } from "fs";
import { unzipSync } from "zlib";
import AdmZip from "adm-zip";

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "vite-plugin" } }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve(JSON.parse(data)));
      res.on("error", reject);
    });
  });
}

function fetchFile(url, dest) {
  return new Promise((resolve, reject) => {
    const follow = (url) => {
      https.get(url, { headers: { "User-Agent": "vite-plugin" } }, (res) => {
        if (res.statusCode === 302 || res.statusCode === 301) {
          return follow(res.headers.location);
        }
        const file = fs.createWriteStream(dest);
        res.pipe(file).on("finish", resolve).on("error", reject);
      });
    };
    follow(url);
  });
}

function copyPdfJs() {
  return {
    name: "copy-pdfjs",
    async closeBundle() {
      const dest      = path.resolve(__dirname, "../../kg/pdfjs");
      const cacheDir  = path.resolve(__dirname, "node_modules/.pdfjs-viewer");
      const versionFile = path.resolve(cacheDir, ".version");

      // Fetch latest release tag from GitHub
      console.log("Checking latest PDF.js release...");
      const release = await fetchJson(
        "https://api.github.com/repos/mozilla/pdf.js/releases/latest"
      );
      const latestTag = release.tag_name; // e.g. "v4.6.82"
      const cachedTag = fs.existsSync(versionFile)
        ? fs.readFileSync(versionFile, "utf8").trim()
        : null;

      if (cachedTag !== latestTag) {
        console.log(`Downloading PDF.js ${latestTag}...`);
        const version = latestTag.replace("v", "");
        const zipUrl  = `https://github.com/mozilla/pdf.js/releases/download/${latestTag}/pdfjs-${version}-dist.zip`;
        const zip     = path.resolve(cacheDir, "pdfjs.zip");

        fs.mkdirSync(cacheDir, { recursive: true });
        await fetchFile(zipUrl, zip);
        const admZip = new AdmZip(zip);
        admZip.extractAllTo(cacheDir, true);
        fs.unlinkSync(zip);
        fs.writeFileSync(versionFile, latestTag);
        console.log(`PDF.js ${latestTag} downloaded and cached.`);
      } else {
        console.log(`PDF.js ${latestTag} already cached.`);
      }

      fs.cpSync(cacheDir, dest, { recursive: true });
      console.log("PDF.js viewer copied to kg/pdfjs/");
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), copyPdfJs()],
  build: {
    outDir: "../../kg",
    emptyOutDir: true,
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    hmr: {
      clientPort: 5173,
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@repo/shadcn-ui/lib/utils": path.resolve("src/lib/utils.js"),
      "@repo/shadcn-ui/components": path.resolve("src/components"),
    },
  },
});