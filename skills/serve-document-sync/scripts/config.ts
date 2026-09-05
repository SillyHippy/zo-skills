// Job configuration for serve document sync
// Each entry maps a Proof job to its target Google Drive folder

export const JOBS = [
  {
    name: "NICOLE DIANE HANSEN",
    proofJobId: "1761606",
    driveFolderId: "1Jt7ebvv7KUpd__iobEtIhiTPqRaqa60W",
  },
  {
    name: "MICHAEL VALENCIA",
    proofJobId: "1761580",
    driveFolderId: "1YZnasMe3leg0to38ZrrYSVbnMBNDgfSy",
  },
  {
    name: "JUSTIN DALE WENZEL",
    proofJobId: "1759774",
    driveFolderId: "1_YZx3JSz9IrOxuH0nDihAj0mQhLGhx-B",
  },
] as const

export const PROOF_BASE_URL = "https://app.proofserve.com"
export const PROOF_USERNAME = process.env.PROOF_USERNAME || "Joseph@JustLegalSolutions.org"
export const PROOF_PASSWORD = process.env.PROOF_PASSWORD || "Crazy8809!"