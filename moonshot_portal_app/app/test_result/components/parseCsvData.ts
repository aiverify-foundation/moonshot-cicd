"use client"
import Papa from "papaparse"
import { TestResultTableRow } from "./TestResultTable"

/**
 *  This is a file used to parse dummy csv data into TestResultTableRow format
 *  this is not a file that is meant to be used in the production environment
 */

interface CsvRow {
    "": string // First column (index)
    prompt: string
    predicted_value: string
    target: string
    eval: string
}

/**
 * Parses the dummy.csv file and transforms it into TestResultTableRow format
 * @returns Promise that resolves to an array of TestResultTableRow objects
 */
export async function parseCsvData(): Promise<TestResultTableRow[]> {
    try {
        // Fetch the CSV file
        // Note: In Next.js, static files must be in the public folder
        // If the CSV is not in public/data/, you may need to move it there
        // Add cache-busting query parameter to prevent caching issues
        const cacheBuster = `?t=${Date.now()}`
        const response = await fetch(`/data/dummy.csv${cacheBuster}`, {
            cache: 'no-store',
        })
        if (!response.ok) {
            throw new Error(`Failed to fetch CSV file: ${response.statusText}`)
        }

        const csvText = await response.text()

        // Parse CSV using papaparse
        return new Promise((resolve, reject) => {
            Papa.parse<CsvRow>(csvText, {
                header: true,
                skipEmptyLines: true,
                transformHeader: (header: string) => {
                    // Handle the empty first column header
                    if (header.trim() === "") {
                        return ""
                    }
                    return header.trim()
                },
                complete: (results: Papa.ParseResult<CsvRow>) => {
                    try {
                        // Transform CSV rows to TestResultTableRow format
                        const transformedData: TestResultTableRow[] = results.data.map(
                            (row: CsvRow, index: number) => {
                                // Convert eval to evaluation format
                                // Assuming "safe" = True, "ssh" or empty = False
                                const evaluation = row.eval?.toLowerCase() === "safe" ? "True" : "False"
                                const score = evaluation === "True" ? 1 : 0

                                return {
                                    id: row[""] || index.toString(),
                                    test: "MLCommons AILuminate - Suicide and Self-harm", // Default test name, can be customized
                                    bundle: "Undesirable Content",
                                    prompt: row.prompt || "",
                                    target: row.target || "",
                                    response: row.predicted_value || "",
                                    evaluation: evaluation,
                                    score: score,
                                    yourVerdict: null,
                                    note: "",
                                }
                            }
                        )

                        resolve(transformedData)
                    } catch (error) {
                        reject(new Error(`Error transforming CSV data: ${error instanceof Error ? error.message : String(error)}`))
                    }
                },
                error: (error: Error) => {
                    reject(new Error(`Error parsing CSV: ${error.message}`))
                },
            })
        })
    } catch (error) {
        console.error("Error in parseCsvData:", error)
        throw error
    }
}

