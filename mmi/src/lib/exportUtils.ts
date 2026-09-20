import * as htmlToImage from 'html-to-image'

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function exportToJson(data: unknown, filename: string): void {
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8;' })
  downloadBlob(blob, filename.endsWith('.json') ? filename : `${filename}.json`)
}

function escapeCsvCell(val: unknown): string {
  if (val === null || val === undefined) return ''
  const str = typeof val === 'object' ? JSON.stringify(val) : String(val)
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export function exportToCsv(
  data: Record<string, unknown>[] | Record<string, unknown>,
  filename: string,
): void {
  let csvContent = ''

  if (Array.isArray(data)) {
    if (data.length === 0) {
      csvContent = 'no_data\n'
    } else {
      const headers = Array.from(
        new Set(data.flatMap((item) => (item && typeof item === 'object' ? Object.keys(item) : []))),
      )
      csvContent += headers.map(escapeCsvCell).join(',') + '\n'
      for (const row of data) {
        csvContent += headers.map((h) => escapeCsvCell(row[h])).join(',') + '\n'
      }
    }
  } else if (data && typeof data === 'object') {
    csvContent = 'key,value\n'
    for (const [key, val] of Object.entries(data)) {
      csvContent += `${escapeCsvCell(key)},${escapeCsvCell(val)}\n`
    }
  }

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, filename.endsWith('.csv') ? filename : `${filename}.csv`)
}

export async function captureElementAsPng(
  element: HTMLElement,
  filename: string,
): Promise<string> {
  // Use html-to-image to generate data URL
  const dataUrl = await htmlToImage.toPng(element, {
    backgroundColor: '#09090b', // dark theme background default
    quality: 0.95,
  })

  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename.endsWith('.png') ? filename : `${filename}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  return dataUrl
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch {
    return false
  }
}

export async function parseJsonFile<T>(
  file: File,
): Promise<{ data: T | null; fileName: string; error: string | null }> {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string
        const data = JSON.parse(text) as T
        resolve({ data, fileName: file.name, error: null })
      } catch {
        resolve({ data: null, fileName: file.name, error: 'Error al decodificar el archivo JSON' })
      }
    }
    reader.onerror = () => {
      resolve({ data: null, fileName: file.name, error: 'Error al leer el archivo' })
    }
    reader.readAsText(file)
  })
}
