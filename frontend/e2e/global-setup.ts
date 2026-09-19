import fs from "node:fs";
import { DATA_DIR } from "./constants";

// Every run starts from "no dashboard data yet".
export default function globalSetup() {
  fs.rmSync(DATA_DIR, { recursive: true, force: true });
  fs.mkdirSync(DATA_DIR, { recursive: true });
}
