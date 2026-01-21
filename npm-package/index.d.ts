/**
 * @gemmology/mineral-data
 *
 * Pre-built SQLite database of 94+ mineral presets with CDL,
 * gemmological properties, and pre-generated 3D models.
 */

/**
 * Absolute path to the minerals.db SQLite database file.
 * Use this for Node.js SQLite libraries like better-sqlite3.
 */
export const dbPath: string;

/**
 * Load the database as an ArrayBuffer for use with sql.js in browsers.
 *
 * @returns Promise resolving to database file as ArrayBuffer
 */
export function dbBuffer(): Promise<ArrayBuffer>;

/**
 * Load the database synchronously as a Buffer.
 *
 * @returns Database file as Node.js Buffer
 */
export function dbBufferSync(): Buffer;

/**
 * Database schema interface for the minerals table.
 */
export interface MineralRecord {
  id: string;
  name: string;
  cdl: string;
  system: string;
  point_group: string;
  chemistry: string;
  hardness: string | null;
  description: string | null;
  sg: string | null;
  ri: string | null;
  birefringence: number | null;
  optical_character: string | null;
  dispersion: number | null;
  lustre: string | null;
  cleavage: string | null;
  fracture: string | null;
  pleochroism: string | null;
  twin_law: string | null;
  phenomenon: string | null;
  note: string | null;
  localities_json: string | null;
  forms_json: string | null;
  colors_json: string | null;
  treatments_json: string | null;
  inclusions_json: string | null;
  /** Pre-generated SVG markup */
  model_svg: string | null;
  /** Pre-generated binary STL data */
  model_stl: ArrayBuffer | null;
  /** Pre-generated glTF JSON */
  model_gltf: string | null;
  /** ISO timestamp when models were generated */
  models_generated_at: string | null;
}
