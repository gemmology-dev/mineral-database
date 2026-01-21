/**
 * @gemmology/mineral-data
 *
 * Pre-built SQLite database of 94+ mineral presets with CDL (Crystal Description Language),
 * gemmological properties, and pre-generated 3D models (SVG, STL, glTF).
 *
 * Usage:
 *   import { dbPath, dbBuffer } from '@gemmology/mineral-data';
 *
 *   // For Node.js file-based access
 *   const db = new Database(dbPath);
 *
 *   // For browser/sql.js usage
 *   const buffer = await dbBuffer();
 *   const db = new SQL.Database(new Uint8Array(buffer));
 */

const path = require('path');
const fs = require('fs');

/**
 * Absolute path to the minerals.db SQLite database file.
 * Use this for Node.js SQLite libraries like better-sqlite3.
 *
 * @type {string}
 */
const dbPath = path.join(__dirname, 'minerals.db');

/**
 * Load the database as an ArrayBuffer for use with sql.js in browsers.
 *
 * @returns {Promise<ArrayBuffer>} Database file as ArrayBuffer
 */
async function dbBuffer() {
  return fs.promises.readFile(dbPath).then(buf => buf.buffer);
}

/**
 * Load the database synchronously as a Buffer.
 *
 * @returns {Buffer} Database file as Node.js Buffer
 */
function dbBufferSync() {
  return fs.readFileSync(dbPath);
}

module.exports = {
  dbPath,
  dbBuffer,
  dbBufferSync,
};
