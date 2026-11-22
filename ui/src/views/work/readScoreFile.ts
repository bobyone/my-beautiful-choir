// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

const MAXIMUM_SIZE = 50 * 1024 * 1024;

/** Encode one file picked by the user without treating its name as a path. */
export async function readScoreFile(file: File): Promise<string> {
  if (file.size < 1 || file.size > MAXIMUM_SIZE) throw new Error("Invalid score file size.");
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => {
      reject(new Error("The selected file could not be read."));
    };
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("The selected file did not produce a data URL."));
        return;
      }
      resolve(reader.result.slice(reader.result.indexOf(",") + 1));
    };
    reader.readAsDataURL(file);
  });
}
