// GENERADO por tools/gen_contract.py a partir de
// contract/schema/dsp_rcp_v0_1.toml. NO EDITAR A MANO.
//
// Contrato DSP↔RCP v1.9 — lado MMI.
//
// Little-endian, empaquetado. Los enteros de 64 bits se exponen como
// bigint: no caben en el double de `number` sin perder enteros a partir
// de 2^53, y un timestamp en nanosegundos los supera de sobra.

/* eslint-disable */

export const MAGIC = 0x4C4D4453;
export const VERSION_MAJOR = 1;
export const VERSION_MINOR = 9;

const LE = true;

/**
 * Cabecera común a todo mensaje.
 */
export interface Header {
  /** 0x4C4D4453. Si no coincide, el flujo no es de este contrato. */
  magic: number;
  /** Incompatible al cambiar. */
  versionMajor: number;
  /** Compatible hacia atrás dentro del mismo major. */
  versionMinor: number;
  /** Ver la tabla de tipos de mensaje. */
  msgType: number;
  /**
   * Banderas de trama. Ver la tabla `header_flag`. El bit 0 declara que
   * la trama viene de una fuente simulada; los demás siguen reservados y valen 0.
   * Un lector no debe exigir que el byte entero sea cero: eso rompería con
   * cualquier bandera futura.
   */
  flags: number;
  /**
   * Bytes que siguen a ESTA cabecera de 12 B, contando la cabecera del mensaje
   * más su carga útil variable si la tiene. Un lector de tramas hace por tanto: leer
   * 12 B, leer payload_len B, y ya tiene el mensaje entero sin conocer su tipo. Para
   * un moment_ray de 4 celdas y 2 momentos vale 88 + 2·(16 + 4·4) = 152, no 64.
   */
  payloadLen: number;
}

export const HEADER_SIZE = 12;

export const HEADER_OFFSETS = {
  magic: 0,
  versionMajor: 4,
  versionMinor: 5,
  msgType: 6,
  flags: 7,
  payloadLen: 8,
} as const;

export function decodeHeader(view: DataView, base = 0): Header {
  return {
    magic: view.getUint32(base + 0, LE),
    versionMajor: view.getUint8(base + 4),
    versionMinor: view.getUint8(base + 5),
    msgType: view.getUint8(base + 6),
    flags: view.getUint8(base + 7),
    payloadLen: view.getUint32(base + 8, LE),
  };
}

export function encodeHeader(value: Header, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(HEADER_SIZE));
  dv.setUint32(base + 0, value.magic, LE);
  dv.setUint8(base + 4, value.versionMajor);
  dv.setUint8(base + 5, value.versionMinor);
  dv.setUint8(base + 6, value.msgType);
  dv.setUint8(base + 7, value.flags);
  dv.setUint32(base + 8, value.payloadLen, LE);
  return dv;
}

/** Tipos de mensaje que viajan sueltos por el cable. */
export const MsgType = {
  /** up */
  MOMENT_RAY: 1,
  /** up */
  SPECTRUM_FRAME: 2,
  /** up */
  STATUS: 3,
  /** up */
  BITE_EVENT: 4,
  /** up */
  CONFIG_ACK: 5,
  /** up */
  SELFTEST_RESULT: 6,
  /** up */
  CAPABILITIES: 7,
  /** down */
  CONFIG: 8,
  /** down */
  CONTROL: 9,
  /** down */
  SELFTEST_REQUEST: 10,
  /** down */
  REQUEST_SPECTRUM: 11,
} as const;

/**
 * Un radial de momentos: la observación autoritativa que el RCP archiva
 * como Level-II y sirve a ORPG.
 *
 * Detrás de esta cabecera van `n_moments` bloques, cada uno formado por un
 * descriptor `moment_field` de 16 B seguido de `n_gates` valores. El tipo de los
 * valores lo dice `moment_field.data_type`; en v0.1 siempre es f32.
 */
export interface MomentRay {
  /** Contador de radiales, envuelve. Detecta pérdidas. */
  seq: number;
  /** Instante del primer pulso del radial en hora de pared, ns desde el epoch UTC. Es el que se archiva en Level-II y se sirve a ORPG. */
  acqTimeUtcNs: bigint;
  /** El mismo instante en el reloj monótono del DSP, ns. Sirve para ordenar y medir intervalos sin que un salto de UTC los corrompa; NO comparable entre procesos. */
  acqMonotonicNs: bigint;
  /** Volumen al que pertenece. Enmarca el archivo Level-II. */
  volumeSeq: number;
  /** Barrido dentro del volumen. */
  sweepSeq: number;
  /** Radial dentro del barrido. */
  rayIndex: number;
  /** Celdas de rango por momento. */
  nGates: number;
  /** Pulsos integrados en este radial. */
  nPulses: number;
  /** Celdas con adquisición correcta. Distinto de que el enlace esté vivo. */
  binsValid: number;
  /** Bloques de momento en la carga útil. */
  nMoments: number;
  /** Ver la enumeración de modos de barrido. */
  sweepMode: number;
  /** Ver la enumeración de modos de dealiasing. */
  prfMode: number;
  /** Ver la tabla de banderas de radial. */
  rayFlags: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
  /** Azimut al abrir el radial, grados. */
  azStartDeg: number;
  /** Azimut al cerrarlo. Con az_start da el ancho barrido. */
  azEndDeg: number;
  /** Elevación al abrir el radial, grados. */
  elStartDeg: number;
  /** Elevación al cerrarlo, grados. */
  elEndDeg: number;
  /** Ángulo nominal del barrido: elevación en PPI, azimut en RHI. */
  fixedAngleDeg: number;
  /** Rango al centro de la primera celda, metros. */
  startRangeM: number;
  /** Separación entre centros de celda, metros. */
  gateSpacingM: number;
  /** PRF efectiva del radial. En dual-PRF, la media. */
  prfHz: number;
  /** Velocidad no ambigua tras dealiasing, m/s. */
  nyquistVelocity: number;
  /** Rango no ambiguo, metros. Es c/(2·PRF) salvo recuperación de trip. */
  unambiguousRangeM: number;
  /** Suelo de ruido vigente al procesar, dBm. */
  noiseFloorDbm: number;
  /** Constante de radar aplicada, dB. El RCP la necesita para rehacer dBZ. */
  radarConstantDb: number;
}

export const MOMENT_RAY_SIZE = 88;

export const MOMENT_RAY_OFFSETS = {
  seq: 0,
  acqTimeUtcNs: 4,
  acqMonotonicNs: 12,
  volumeSeq: 20,
  sweepSeq: 24,
  rayIndex: 26,
  nGates: 28,
  nPulses: 30,
  binsValid: 32,
  nMoments: 34,
  sweepMode: 35,
  prfMode: 36,
  rayFlags: 37,
  pad0: 38,
  azStartDeg: 40,
  azEndDeg: 44,
  elStartDeg: 48,
  elEndDeg: 52,
  fixedAngleDeg: 56,
  startRangeM: 60,
  gateSpacingM: 64,
  prfHz: 68,
  nyquistVelocity: 72,
  unambiguousRangeM: 76,
  noiseFloorDbm: 80,
  radarConstantDb: 84,
} as const;

export function decodeMomentRay(view: DataView, base = 0): MomentRay {
  return {
    seq: view.getUint32(base + 0, LE),
    acqTimeUtcNs: view.getBigUint64(base + 4, LE),
    acqMonotonicNs: view.getBigUint64(base + 12, LE),
    volumeSeq: view.getUint32(base + 20, LE),
    sweepSeq: view.getUint16(base + 24, LE),
    rayIndex: view.getUint16(base + 26, LE),
    nGates: view.getUint16(base + 28, LE),
    nPulses: view.getUint16(base + 30, LE),
    binsValid: view.getUint16(base + 32, LE),
    nMoments: view.getUint8(base + 34),
    sweepMode: view.getUint8(base + 35),
    prfMode: view.getUint8(base + 36),
    rayFlags: view.getUint8(base + 37),
    pad0: view.getUint16(base + 38, LE),
    azStartDeg: view.getFloat32(base + 40, LE),
    azEndDeg: view.getFloat32(base + 44, LE),
    elStartDeg: view.getFloat32(base + 48, LE),
    elEndDeg: view.getFloat32(base + 52, LE),
    fixedAngleDeg: view.getFloat32(base + 56, LE),
    startRangeM: view.getFloat32(base + 60, LE),
    gateSpacingM: view.getFloat32(base + 64, LE),
    prfHz: view.getFloat32(base + 68, LE),
    nyquistVelocity: view.getFloat32(base + 72, LE),
    unambiguousRangeM: view.getFloat32(base + 76, LE),
    noiseFloorDbm: view.getFloat32(base + 80, LE),
    radarConstantDb: view.getFloat32(base + 84, LE),
  };
}

export function encodeMomentRay(value: MomentRay, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(MOMENT_RAY_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setBigUint64(base + 4, value.acqTimeUtcNs, LE);
  dv.setBigUint64(base + 12, value.acqMonotonicNs, LE);
  dv.setUint32(base + 20, value.volumeSeq, LE);
  dv.setUint16(base + 24, value.sweepSeq, LE);
  dv.setUint16(base + 26, value.rayIndex, LE);
  dv.setUint16(base + 28, value.nGates, LE);
  dv.setUint16(base + 30, value.nPulses, LE);
  dv.setUint16(base + 32, value.binsValid, LE);
  dv.setUint8(base + 34, value.nMoments);
  dv.setUint8(base + 35, value.sweepMode);
  dv.setUint8(base + 36, value.prfMode);
  dv.setUint8(base + 37, value.rayFlags);
  dv.setUint16(base + 38, value.pad0, LE);
  dv.setFloat32(base + 40, value.azStartDeg, LE);
  dv.setFloat32(base + 44, value.azEndDeg, LE);
  dv.setFloat32(base + 48, value.elStartDeg, LE);
  dv.setFloat32(base + 52, value.elEndDeg, LE);
  dv.setFloat32(base + 56, value.fixedAngleDeg, LE);
  dv.setFloat32(base + 60, value.startRangeM, LE);
  dv.setFloat32(base + 64, value.gateSpacingM, LE);
  dv.setFloat32(base + 68, value.prfHz, LE);
  dv.setFloat32(base + 72, value.nyquistVelocity, LE);
  dv.setFloat32(base + 76, value.unambiguousRangeM, LE);
  dv.setFloat32(base + 80, value.noiseFloorDbm, LE);
  dv.setFloat32(base + 84, value.radarConstantDb, LE);
  return dv;
}

/**
 * Descriptor de un momento dentro de la carga útil de un moment_ray.
 *
 * No viaja suelto: siempre va incrustado, y por eso su type_id es 0. Detrás de
 * cada descriptor van `n_gates` valores del tipo que indica `data_type`.
 */
export interface MomentField {
  /** Qué momento es. Ver la enumeración de momentos. */
  kind: number;
  /** Codificación de los valores. En v0.1 siempre f32. */
  dataType: number;
  /** Ver la tabla de banderas de momento. */
  flags: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
  /** Valores que siguen. Tiene que coincidir con el n_gates del radial. */
  nGates: number;
  /** Factor de escala. Vale 1.0 con data_type f32. */
  scale: number;
  /** Desplazamiento. Vale 0.0 con data_type f32. */
  offset: number;
}

export const MOMENT_FIELD_SIZE = 16;

export const MOMENT_FIELD_OFFSETS = {
  kind: 0,
  dataType: 1,
  flags: 2,
  pad0: 3,
  nGates: 4,
  scale: 8,
  offset: 12,
} as const;

export function decodeMomentField(view: DataView, base = 0): MomentField {
  return {
    kind: view.getUint8(base + 0),
    dataType: view.getUint8(base + 1),
    flags: view.getUint8(base + 2),
    pad0: view.getUint8(base + 3),
    nGates: view.getUint32(base + 4, LE),
    scale: view.getFloat32(base + 8, LE),
    offset: view.getFloat32(base + 12, LE),
  };
}

export function encodeMomentField(value: MomentField, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(MOMENT_FIELD_SIZE));
  dv.setUint8(base + 0, value.kind);
  dv.setUint8(base + 1, value.dataType);
  dv.setUint8(base + 2, value.flags);
  dv.setUint8(base + 3, value.pad0);
  dv.setUint32(base + 4, value.nGates, LE);
  dv.setFloat32(base + 8, value.scale, LE);
  dv.setFloat32(base + 12, value.offset, LE);
  return dv;
}

/**
 * Traza del analizador de espectro de FI. Detrás van `n_bins` valores f32
 * en dB, de menor a mayor frecuencia.
 */
export interface SpectrumFrame {
  /** Contador de tramas, envuelve. */
  seq: number;
  /** Instante de la captura en hora de pared, ns desde el epoch UTC. */
  captureTimeUtcNs: bigint;
  /** Puntos de la traza. */
  nBins: number;
  /** Canal de recepción al que corresponde. */
  channel: number;
  /** Reservado en v0.1; vale 0. */
  flags: number;
  /** Frecuencia central de la traza, Hz. */
  centerFreqHz: number;
  /** Anchura total barrida, Hz. */
  spanHz: number;
  /** Nivel de referencia, dBm. */
  refLevelDbm: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
}

export const SPECTRUM_FRAME_SIZE = 32;

export const SPECTRUM_FRAME_OFFSETS = {
  seq: 0,
  captureTimeUtcNs: 4,
  nBins: 12,
  channel: 14,
  flags: 15,
  centerFreqHz: 16,
  spanHz: 20,
  refLevelDbm: 24,
  pad0: 28,
} as const;

export function decodeSpectrumFrame(view: DataView, base = 0): SpectrumFrame {
  return {
    seq: view.getUint32(base + 0, LE),
    captureTimeUtcNs: view.getBigUint64(base + 4, LE),
    nBins: view.getUint16(base + 12, LE),
    channel: view.getUint8(base + 14),
    flags: view.getUint8(base + 15),
    centerFreqHz: view.getFloat32(base + 16, LE),
    spanHz: view.getFloat32(base + 20, LE),
    refLevelDbm: view.getFloat32(base + 24, LE),
    pad0: view.getUint32(base + 28, LE),
  };
}

export function encodeSpectrumFrame(value: SpectrumFrame, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(SPECTRUM_FRAME_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setBigUint64(base + 4, value.captureTimeUtcNs, LE);
  dv.setUint16(base + 12, value.nBins, LE);
  dv.setUint8(base + 14, value.channel);
  dv.setUint8(base + 15, value.flags);
  dv.setFloat32(base + 16, value.centerFreqHz, LE);
  dv.setFloat32(base + 20, value.spanHz, LE);
  dv.setFloat32(base + 24, value.refLevelDbm, LE);
  dv.setUint32(base + 28, value.pad0, LE);
  return dv;
}

/**
 * Salud y telemetría. Se emite periódicamente y ante cualquier cambio de
 * estado.
 *
 * Deliberadamente no colapsa en un bit de vivo/muerto: lleva completitud de datos
 * (bins_ok frente a bins_total), deriva del periodo de disparo (medido frente a
 * mandado) y lectura de suelo de ruido y offset de continua por canal, que son las
 * tres cosas que el plan (§6.1) exige poder vigilar por separado.
 */
export interface Status {
  /** Segundos desde el arranque del servicio. */
  uptimeS: number;
  /** Fase vigente: configuración o marcha. Ver la enumeración. */
  phase: number;
  /** Severidad agregada. Ver la enumeración. */
  severity: number;
  /** Último código de error del plano de control. */
  lastError: number;
  /** Canales de recepción con lectura válida en este mensaje. */
  nRxChannels: number;
  /** Modos de proceso disponibles ahora mismo. */
  capabilityFlags: number;
  /** Ver la tabla de banderas de BITE. */
  biteFlags: number;
  /** `seq` de la configuración vigente. Permite confirmar qué se aplicó. */
  configSeq: number;
  /** Radiales recibidos del DRx. */
  raysIn: number;
  /** Radiales de momentos emitidos al RCP. */
  raysOut: number;
  /** Radiales descartados por contrapresión o trama mala. */
  raysDropped: number;
  /** Ocupación de la cola de ingesta, en radiales. */
  queueDepth: number;
  /** Celdas adquiridas correctamente desde el último reset. */
  binsOk: number;
  /** Celdas esperadas en el mismo intervalo. */
  binsTotal: number;
  /** Periodo de disparo mandado, ns. */
  triggerPeriodCmdNs: number;
  /** Periodo de disparo medido, ns. La diferencia es la deriva. */
  triggerPeriodMeasNs: number;
  /** Frecuencia del burst medida en esta actualización del lazo de AFC (`lamula_burst::AfcUpdate::freq_meas_hz`), sin filtrar. Congelada en el último valor válido mientras `afc_bite` esté a 1. 0 sin lazo de AFC corriendo (sólo magnetrón, `burst_window_bins > 0` en `config`). Consume el relleno explícito v1.3 (`pad0`), mismo tamaño. */
  afcFreqMeasHz: number;
  /** Suelo de ruido del canal 0, dBm. */
  noiseFloorDbm0: number;
  /** Suelo de ruido del canal 1, dBm. */
  noiseFloorDbm1: number;
  /** Suelo de ruido del canal 2, dBm. */
  noiseFloorDbm2: number;
  /** Suelo de ruido del canal 3, dBm. */
  noiseFloorDbm3: number;
  /** Offset de continua en I, canal 0. */
  dcOffsetI0: number;
  /** Offset de continua en I, canal 1. */
  dcOffsetI1: number;
  /** Offset de continua en I, canal 2. */
  dcOffsetI2: number;
  /** Offset de continua en I, canal 3. */
  dcOffsetI3: number;
  /** Offset de continua en Q, canal 0. */
  dcOffsetQ0: number;
  /** Offset de continua en Q, canal 1. */
  dcOffsetQ1: number;
  /** Offset de continua en Q, canal 2. */
  dcOffsetQ2: number;
  /** Offset de continua en Q, canal 3. */
  dcOffsetQ3: number;
  /** Offset de frecuencia filtrado que el lazo de AFC aplica esta actualización (`lamula_burst::AfcUpdate::freq_hz`) — el valor de control realmente enviado al NCO del DRx vía el mensaje `Afc` (`nco_phase_inc`). 0 sin lazo de AFC corriendo. Nuevo en v1.4, aditivo. */
  afcControlFreqHz: number;
  /** Amplitud media del burst medida esta actualización (`lamula_burst::AfcUpdate::amplitude`). Unidad lineal/relativa del receptor, **no** dBm calibrado — no existe conversión a dBm para este canal en este workspace. 0 sin lazo de AFC corriendo. Nuevo en v1.4, aditivo. */
  afcBurstAmplitude: number;
  /** 1 si esta actualización del lazo de AFC se congeló por pérdida de burst (`lamula_burst::AfcUpdate::bite`), 0 en otro caso o sin lazo corriendo. La máquina de estados con histéresis (Disabled/Manual/NoBurst/Wait/Track/Locked) no existe todavía — sólo este bit binario. Nuevo en v1.4, aditivo. */
  afcBite: number;
}

export const STATUS_SIZE = 113;

export const STATUS_OFFSETS = {
  uptimeS: 0,
  phase: 4,
  severity: 5,
  lastError: 6,
  nRxChannels: 7,
  capabilityFlags: 8,
  biteFlags: 12,
  configSeq: 16,
  raysIn: 20,
  raysOut: 24,
  raysDropped: 28,
  queueDepth: 32,
  binsOk: 36,
  binsTotal: 40,
  triggerPeriodCmdNs: 44,
  triggerPeriodMeasNs: 48,
  afcFreqMeasHz: 52,
  noiseFloorDbm0: 56,
  noiseFloorDbm1: 60,
  noiseFloorDbm2: 64,
  noiseFloorDbm3: 68,
  dcOffsetI0: 72,
  dcOffsetI1: 76,
  dcOffsetI2: 80,
  dcOffsetI3: 84,
  dcOffsetQ0: 88,
  dcOffsetQ1: 92,
  dcOffsetQ2: 96,
  dcOffsetQ3: 100,
  afcControlFreqHz: 104,
  afcBurstAmplitude: 108,
  afcBite: 112,
} as const;

export function decodeStatus(view: DataView, base = 0): Status {
  return {
    uptimeS: view.getUint32(base + 0, LE),
    phase: view.getUint8(base + 4),
    severity: view.getUint8(base + 5),
    lastError: view.getUint8(base + 6),
    nRxChannels: view.getUint8(base + 7),
    capabilityFlags: view.getUint32(base + 8, LE),
    biteFlags: view.getUint32(base + 12, LE),
    configSeq: view.getUint32(base + 16, LE),
    raysIn: view.getUint32(base + 20, LE),
    raysOut: view.getUint32(base + 24, LE),
    raysDropped: view.getUint32(base + 28, LE),
    queueDepth: view.getUint32(base + 32, LE),
    binsOk: view.getUint32(base + 36, LE),
    binsTotal: view.getUint32(base + 40, LE),
    triggerPeriodCmdNs: view.getUint32(base + 44, LE),
    triggerPeriodMeasNs: view.getUint32(base + 48, LE),
    afcFreqMeasHz: view.getFloat32(base + 52, LE),
    noiseFloorDbm0: view.getFloat32(base + 56, LE),
    noiseFloorDbm1: view.getFloat32(base + 60, LE),
    noiseFloorDbm2: view.getFloat32(base + 64, LE),
    noiseFloorDbm3: view.getFloat32(base + 68, LE),
    dcOffsetI0: view.getFloat32(base + 72, LE),
    dcOffsetI1: view.getFloat32(base + 76, LE),
    dcOffsetI2: view.getFloat32(base + 80, LE),
    dcOffsetI3: view.getFloat32(base + 84, LE),
    dcOffsetQ0: view.getFloat32(base + 88, LE),
    dcOffsetQ1: view.getFloat32(base + 92, LE),
    dcOffsetQ2: view.getFloat32(base + 96, LE),
    dcOffsetQ3: view.getFloat32(base + 100, LE),
    afcControlFreqHz: view.getFloat32(base + 104, LE),
    afcBurstAmplitude: view.getFloat32(base + 108, LE),
    afcBite: view.getUint8(base + 112),
  };
}

export function encodeStatus(value: Status, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(STATUS_SIZE));
  dv.setUint32(base + 0, value.uptimeS, LE);
  dv.setUint8(base + 4, value.phase);
  dv.setUint8(base + 5, value.severity);
  dv.setUint8(base + 6, value.lastError);
  dv.setUint8(base + 7, value.nRxChannels);
  dv.setUint32(base + 8, value.capabilityFlags, LE);
  dv.setUint32(base + 12, value.biteFlags, LE);
  dv.setUint32(base + 16, value.configSeq, LE);
  dv.setUint32(base + 20, value.raysIn, LE);
  dv.setUint32(base + 24, value.raysOut, LE);
  dv.setUint32(base + 28, value.raysDropped, LE);
  dv.setUint32(base + 32, value.queueDepth, LE);
  dv.setUint32(base + 36, value.binsOk, LE);
  dv.setUint32(base + 40, value.binsTotal, LE);
  dv.setUint32(base + 44, value.triggerPeriodCmdNs, LE);
  dv.setUint32(base + 48, value.triggerPeriodMeasNs, LE);
  dv.setFloat32(base + 52, value.afcFreqMeasHz, LE);
  dv.setFloat32(base + 56, value.noiseFloorDbm0, LE);
  dv.setFloat32(base + 60, value.noiseFloorDbm1, LE);
  dv.setFloat32(base + 64, value.noiseFloorDbm2, LE);
  dv.setFloat32(base + 68, value.noiseFloorDbm3, LE);
  dv.setFloat32(base + 72, value.dcOffsetI0, LE);
  dv.setFloat32(base + 76, value.dcOffsetI1, LE);
  dv.setFloat32(base + 80, value.dcOffsetI2, LE);
  dv.setFloat32(base + 84, value.dcOffsetI3, LE);
  dv.setFloat32(base + 88, value.dcOffsetQ0, LE);
  dv.setFloat32(base + 92, value.dcOffsetQ1, LE);
  dv.setFloat32(base + 96, value.dcOffsetQ2, LE);
  dv.setFloat32(base + 100, value.dcOffsetQ3, LE);
  dv.setFloat32(base + 104, value.afcControlFreqHz, LE);
  dv.setFloat32(base + 108, value.afcBurstAmplitude, LE);
  dv.setUint8(base + 112, value.afcBite);
  return dv;
}

/**
 * Un suceso de BITE con su instante. Detrás van `text_len` bytes UTF-8 de
 * texto libre para diagnóstico; el código es lo que se filtra y se historia, el
 * texto es para el operador.
 */
export interface BiteEvent {
  /** Instante del suceso en hora de pared, ns desde el epoch UTC. Lo lee un operador, así que nunca es monótono. */
  eventTimeUtcNs: bigint;
  /** Código del catálogo de fallos. */
  code: number;
  /** Valor asociado; su sentido depende del código. */
  value: number;
  /** Ver la enumeración de severidad. */
  severity: number;
  /** Componente del pipeline que lo emite. */
  subsystem: number;
  /** Bytes UTF-8 de texto detrás de la cabecera. */
  textLen: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
}

export const BITE_EVENT_SIZE = 20;

export const BITE_EVENT_OFFSETS = {
  eventTimeUtcNs: 0,
  code: 8,
  value: 12,
  severity: 16,
  subsystem: 17,
  textLen: 18,
  pad0: 19,
} as const;

export function decodeBiteEvent(view: DataView, base = 0): BiteEvent {
  return {
    eventTimeUtcNs: view.getBigUint64(base + 0, LE),
    code: view.getUint32(base + 8, LE),
    value: view.getUint32(base + 12, LE),
    severity: view.getUint8(base + 16),
    subsystem: view.getUint8(base + 17),
    textLen: view.getUint8(base + 18),
    pad0: view.getUint8(base + 19),
  };
}

export function encodeBiteEvent(value: BiteEvent, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(BITE_EVENT_SIZE));
  dv.setBigUint64(base + 0, value.eventTimeUtcNs, LE);
  dv.setUint32(base + 8, value.code, LE);
  dv.setUint32(base + 12, value.value, LE);
  dv.setUint8(base + 16, value.severity);
  dv.setUint8(base + 17, value.subsystem);
  dv.setUint8(base + 18, value.textLen);
  dv.setUint8(base + 19, value.pad0);
  return dv;
}

/**
 * Respuesta a un config. `error` distinto de 0 significa que NO se aplicó
 * nada y que la configuración anterior sigue vigente.
 */
export interface ConfigAck {
  /** El `seq` del config al que responde. */
  seq: number;
  /** Código de error; 0 es aceptado. */
  error: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
  /** Relleno explícito; vale 0. */
  pad1: number;
}

export const CONFIG_ACK_SIZE = 8;

export const CONFIG_ACK_OFFSETS = {
  seq: 0,
  error: 4,
  pad0: 5,
  pad1: 6,
} as const;

export function decodeConfigAck(view: DataView, base = 0): ConfigAck {
  return {
    seq: view.getUint32(base + 0, LE),
    error: view.getUint8(base + 4),
    pad0: view.getUint8(base + 5),
    pad1: view.getUint16(base + 6, LE),
  };
}

export function encodeConfigAck(value: ConfigAck, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(CONFIG_ACK_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setUint8(base + 4, value.error);
  dv.setUint8(base + 5, value.pad0);
  dv.setUint16(base + 6, value.pad1, LE);
  return dv;
}

/**
 * Resultado del autotest de enlace. El plan (§6.1) lo exige en cada
 * reconexión del RCP: un apretón de manos TCP no basta para fiarse del enlace
 * para control.
 */
export interface SelftestResult {
  /** El `seq` de la petición a la que responde. */
  seq: number;
  /** El nonce de la petición, devuelto tal cual. */
  nonce: number;
  /** Modos de proceso disponibles. */
  capabilityFlags: number;
  /** Código de error; 0 es enlace apto para control. */
  error: number;
  /** Versión de contrato que habla el DSP. */
  versionMajor: number;
  /** Versión de contrato que habla el DSP. */
  versionMinor: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
}

export const SELFTEST_RESULT_SIZE = 16;

export const SELFTEST_RESULT_OFFSETS = {
  seq: 0,
  nonce: 4,
  capabilityFlags: 8,
  error: 12,
  versionMajor: 13,
  versionMinor: 14,
  pad0: 15,
} as const;

export function decodeSelftestResult(view: DataView, base = 0): SelftestResult {
  return {
    seq: view.getUint32(base + 0, LE),
    nonce: view.getUint32(base + 4, LE),
    capabilityFlags: view.getUint32(base + 8, LE),
    error: view.getUint8(base + 12),
    versionMajor: view.getUint8(base + 13),
    versionMinor: view.getUint8(base + 14),
    pad0: view.getUint8(base + 15),
  };
}

export function encodeSelftestResult(value: SelftestResult, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(SELFTEST_RESULT_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setUint32(base + 4, value.nonce, LE);
  dv.setUint32(base + 8, value.capabilityFlags, LE);
  dv.setUint8(base + 12, value.error);
  dv.setUint8(base + 13, value.versionMajor);
  dv.setUint8(base + 14, value.versionMinor);
  dv.setUint8(base + 15, value.pad0);
  return dv;
}

/**
 * Qué sabe hacer esta compilación del DSP. Se responde a un control con
 * mandato `request_capabilities`, y es lo que permite al RCP no ofrecer al
 * operador un modo que el procesador no implementa.
 */
export interface Capabilities {
  /** Momentos que este DSP puede producir, un bit por momento. */
  momentMask: number;
  /** Modos de dealiasing disponibles, un bit por modo. */
  dealiasMask: number;
  /** Estimadores disponibles, un bit por estimador. */
  estimatorMask: number;
  /** Celdas de rango máximas por radial. */
  maxGates: number;
  /** Pulsos máximos integrables por radial. */
  maxPulses: number;
  /** Canales de recepción que procesa. */
  nRxChannels: number;
  /** Anchura del acumulador de fase del NCO de recepción del DRx, bits (`lamula_burst::nco_phase_inc_for_freq_offset`). Constante de instalación, no medida; publicada para que el RCP pueda verificarla contra la especificación del DRx en vez de confiar a ciegas en la variable de entorno del DSP que la fija. Consume el relleno explícito v1.7 (`pad0`), mismo tamaño. */
  rxNcoWordBits: number;
  /** Frecuencia intermedia de transmisión, Hz. Constante de instalación, no medida — mapeo RCP entrada 3. */
  txIfHz: number;
  /** Frecuencia intermedia de recepción, Hz. Constante de instalación, no medida. Es `spectrum_frame.center_freq_hz` (`crate::ray::build_spectrum_frame`): antes salía en 0 por falta de este dato. */
  rxIfHz: number;
  /** Frecuencia de referencia del NCO de recepción del DRx, Hz (`ServiceConfig::drx_nco_fs_hz`). Publicada por el mismo motivo que `rx_nco_word_bits`: hoy es variable de entorno sin forma de verificarla contra el DRx real. */
  rxNcoFsHz: number;
}

export const CAPABILITIES_SIZE = 32;

export const CAPABILITIES_OFFSETS = {
  momentMask: 0,
  dealiasMask: 4,
  estimatorMask: 8,
  maxGates: 12,
  maxPulses: 16,
  nRxChannels: 18,
  rxNcoWordBits: 19,
  txIfHz: 20,
  rxIfHz: 24,
  rxNcoFsHz: 28,
} as const;

export function decodeCapabilities(view: DataView, base = 0): Capabilities {
  return {
    momentMask: view.getUint32(base + 0, LE),
    dealiasMask: view.getUint32(base + 4, LE),
    estimatorMask: view.getUint32(base + 8, LE),
    maxGates: view.getUint32(base + 12, LE),
    maxPulses: view.getUint16(base + 16, LE),
    nRxChannels: view.getUint8(base + 18),
    rxNcoWordBits: view.getUint8(base + 19),
    txIfHz: view.getFloat32(base + 20, LE),
    rxIfHz: view.getFloat32(base + 24, LE),
    rxNcoFsHz: view.getFloat32(base + 28, LE),
  };
}

export function encodeCapabilities(value: Capabilities, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(CAPABILITIES_SIZE));
  dv.setUint32(base + 0, value.momentMask, LE);
  dv.setUint32(base + 4, value.dealiasMask, LE);
  dv.setUint32(base + 8, value.estimatorMask, LE);
  dv.setUint32(base + 12, value.maxGates, LE);
  dv.setUint16(base + 16, value.maxPulses, LE);
  dv.setUint8(base + 18, value.nRxChannels);
  dv.setUint8(base + 19, value.rxNcoWordBits);
  dv.setFloat32(base + 20, value.txIfHz, LE);
  dv.setFloat32(base + 24, value.rxIfHz, LE);
  dv.setFloat32(base + 28, value.rxNcoFsHz, LE);
  return dv;
}

/**
 * Configuración completa. Se aplica de forma atómica: o entra entera o se
 * rechaza entera y el estado anterior se preserva.
 *
 * Sólo se acepta en fase de configuración. En marcha se rechaza con
 * `not_in_setup_phase`: el plan (§6.1) exige que aplicar configuración y arrancar
 * la adquisición sean pasos distintos, y no que la configuración se cuele a mitad
 * del flujo.
 */
export interface Config {
  /** Se devuelve tal cual en el config_ack. */
  seq: number;
  /** Momentos a emitir, un bit por momento. */
  momentMask: number;
  /** Pulsos a integrar por radial. */
  nPulses: number;
  /** Celdas de rango por radial. */
  nGates: number;
  /** Filtro de clutter. Ver la enumeración. */
  clutterFilter: number;
  /** Modo de dealiasing de velocidad. Ver la enumeración. */
  dealiasMode: number;
  /** Modo de barrido. Ver la enumeración. */
  sweepMode: number;
  /** Estimador de momentos. Ver la enumeración. */
  estimator: number;
  /** Filtrado de interferencia de banda estrecha: 0 no, 1 sí. */
  rfiFilter: number;
  /** Método de recuperación/detección de trip múltiple. Ver la enumeración `range_dealias_mode`. */
  rangeDealiasMode: number;
  /** Numerador de la razón dual-PRF; 0 si no aplica. */
  prfRatioNum: number;
  /** Denominador de la razón dual-PRF; 0 si no aplica. */
  prfRatioDen: number;
  /** Rango de la primera celda, metros. */
  startRangeM: number;
  /** Separación entre celdas, metros. Fija el tamaño de celda. */
  gateSpacingM: number;
  /** PRF pedida, Hz. Se valida contra la extensión de rango. */
  prfHz: number;
  /** Umbral de SQI por debajo del cual se censura la celda. */
  sqiThreshold: number;
  /** Umbral de señal sobre ruido, dB. */
  sigThreshold: number;
  /** Umbral de corrección de clutter, dB. */
  ccorThreshold: number;
  /** Umbral logarítmico de potencia, dB. */
  logThreshold: number;
  /** Anchura espectral asumida del clutter, m/s. */
  clutterWidthMs: number;
  /** Constante de radar, dB. */
  radarConstantDb: number;
  /** Suelo de ruido de referencia, dBm. */
  noiseFloorDbm: number;
  /** Ganancia del receptor, dB. */
  receiverGainDb: number;
  /** Corrección de sesgo de ZDR, dB. */
  zdrOffsetDb: number;
  /** Fase diferencial del sistema a restar, grados. */
  phidpOffsetDeg: number;
  /** Aislamiento cruzado de la antena, dB. Satura ldr_db (lamula_polarimetry::ldr_db); sin efecto salvo LDR. */
  antennaIsolationDb: number;
  /** Longitud de onda, metros. Escala la velocidad. */
  wavelengthM: number;
  /** Modo del segundo canal de recepción cuando n_rx_channels > 1. Ver la enumeración. Sin efecto con canal único. */
  polarizationMode: number;
  /** Tipo de transmisor de esta instalación. Ver la enumeración `transmitter_type`. Reemplaza la constante local `MAGNETRON_TRANSMITTER` de `crates/service::ray` — el parque es mixto, magnetrón y klistrón conviven, así que no se puede fijar en tiempo de compilación. De este campo depende qué vía de recuperación de segundo trip aplica (fase aleatoria frente a SZ(8/64)), si la corrección de fase por burst es obligatoria u opcional, y qué controles puede ofrecer el MMI sin invitar a un error de instalación. Consume el relleno explícito v1.5 (`pad0`), mismo tamaño. */
  transmitterType: number;
  /** Bins iniciales de un canal de burst (drx_dsp::channel::TX_BURST_0/1) que llevan señal real; el resto del canal es ruido/silencio. 0 si la instalación no tiene canal de burst (transmisor coherente sin monitor de burst). */
  burstWindowBins: number;
  /** Índice en la tabla de anchos de pulso del DRx (drx_dsp::Config.pulse_width_idx). Relay directo: el DSP no conoce los límites de la tabla, sólo el DRx. Escribible (E5/E6, decisión mapeo-parametros-dsp.md#15). Pendiente de cablear hacia drx_dsp::Config — ver doc-comment de crate::main en el binario del servicio. */
  pulseWidthIdx: number;
  /** 0 = celda fina, 1 = celda gruesa (drx_dsp::Config.cell_mode). Relay directo. Mismo pendiente de cableado que pulse_width_idx. */
  cellMode: number;
  /** Divisor de PRF del DRx; PRF = FS_HZ/prf_div (drx_dsp::Config.prf_div). Entero puro, sin conversión de unidades — a diferencia de trigger_delay_N/trigger_width_N, no depende de FS_HZ del DRx. Mismo pendiente de cableado que pulse_width_idx. */
  prfDiv: number;
  /** Retardo del trigger 0, microsegundos. drx_dsp::Config.trigger_delay_0 lo expresa en ciclos de fs del DRx; la conversión ciclos↔µs vive en el DSP (nuevo parámetro de instalación, no en ningún contrato — ver ServiceConfig::drx_trigger_fs_hz), no en el RCP, para no exponerle el reloj del DRx. Reabre en parte D-02 (ver doc-comment de drx_dsp::Afc) sólo para temporizado de trigger, no para el lazo de AFC, que sigue viajando como palabra de fase. Reabierto por decisión explícita (plan-pendientes-drx-dsp.md): F1 del MMI legacy pide esta unidad. Mismo pendiente de cableado que pulse_width_idx. */
  triggerDelay0: number;
  /** Retardo del trigger 1, microsegundos. Ver trigger_delay_0. */
  triggerDelay1: number;
  /** Retardo del trigger 2, microsegundos. Ver trigger_delay_0. */
  triggerDelay2: number;
  /** Retardo del trigger 3, microsegundos. Ver trigger_delay_0. */
  triggerDelay3: number;
  /** Ancho del trigger 0, microsegundos. Misma conversión y mismo pendiente que trigger_delay_0. */
  triggerWidth0: number;
  /** Ancho del trigger 1, microsegundos. Ver trigger_width_0. */
  triggerWidth1: number;
  /** Ancho del trigger 2, microsegundos. Ver trigger_width_0. */
  triggerWidth2: number;
  /** Ancho del trigger 3, microsegundos. Ver trigger_width_0. */
  triggerWidth3: number;
}

export const CONFIG_SIZE = 122;

export const CONFIG_OFFSETS = {
  seq: 0,
  momentMask: 4,
  nPulses: 8,
  nGates: 10,
  clutterFilter: 12,
  dealiasMode: 13,
  sweepMode: 14,
  estimator: 15,
  rfiFilter: 16,
  rangeDealiasMode: 17,
  prfRatioNum: 18,
  prfRatioDen: 19,
  startRangeM: 20,
  gateSpacingM: 24,
  prfHz: 28,
  sqiThreshold: 32,
  sigThreshold: 36,
  ccorThreshold: 40,
  logThreshold: 44,
  clutterWidthMs: 48,
  radarConstantDb: 52,
  noiseFloorDbm: 56,
  receiverGainDb: 60,
  zdrOffsetDb: 64,
  phidpOffsetDeg: 68,
  antennaIsolationDb: 72,
  wavelengthM: 76,
  polarizationMode: 80,
  transmitterType: 81,
  burstWindowBins: 82,
  pulseWidthIdx: 84,
  cellMode: 85,
  prfDiv: 86,
  triggerDelay0: 90,
  triggerDelay1: 94,
  triggerDelay2: 98,
  triggerDelay3: 102,
  triggerWidth0: 106,
  triggerWidth1: 110,
  triggerWidth2: 114,
  triggerWidth3: 118,
} as const;

export function decodeConfig(view: DataView, base = 0): Config {
  return {
    seq: view.getUint32(base + 0, LE),
    momentMask: view.getUint32(base + 4, LE),
    nPulses: view.getUint16(base + 8, LE),
    nGates: view.getUint16(base + 10, LE),
    clutterFilter: view.getUint8(base + 12),
    dealiasMode: view.getUint8(base + 13),
    sweepMode: view.getUint8(base + 14),
    estimator: view.getUint8(base + 15),
    rfiFilter: view.getUint8(base + 16),
    rangeDealiasMode: view.getUint8(base + 17),
    prfRatioNum: view.getUint8(base + 18),
    prfRatioDen: view.getUint8(base + 19),
    startRangeM: view.getFloat32(base + 20, LE),
    gateSpacingM: view.getFloat32(base + 24, LE),
    prfHz: view.getFloat32(base + 28, LE),
    sqiThreshold: view.getFloat32(base + 32, LE),
    sigThreshold: view.getFloat32(base + 36, LE),
    ccorThreshold: view.getFloat32(base + 40, LE),
    logThreshold: view.getFloat32(base + 44, LE),
    clutterWidthMs: view.getFloat32(base + 48, LE),
    radarConstantDb: view.getFloat32(base + 52, LE),
    noiseFloorDbm: view.getFloat32(base + 56, LE),
    receiverGainDb: view.getFloat32(base + 60, LE),
    zdrOffsetDb: view.getFloat32(base + 64, LE),
    phidpOffsetDeg: view.getFloat32(base + 68, LE),
    antennaIsolationDb: view.getFloat32(base + 72, LE),
    wavelengthM: view.getFloat32(base + 76, LE),
    polarizationMode: view.getUint8(base + 80),
    transmitterType: view.getUint8(base + 81),
    burstWindowBins: view.getUint16(base + 82, LE),
    pulseWidthIdx: view.getUint8(base + 84),
    cellMode: view.getUint8(base + 85),
    prfDiv: view.getUint32(base + 86, LE),
    triggerDelay0: view.getFloat32(base + 90, LE),
    triggerDelay1: view.getFloat32(base + 94, LE),
    triggerDelay2: view.getFloat32(base + 98, LE),
    triggerDelay3: view.getFloat32(base + 102, LE),
    triggerWidth0: view.getFloat32(base + 106, LE),
    triggerWidth1: view.getFloat32(base + 110, LE),
    triggerWidth2: view.getFloat32(base + 114, LE),
    triggerWidth3: view.getFloat32(base + 118, LE),
  };
}

export function encodeConfig(value: Config, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(CONFIG_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setUint32(base + 4, value.momentMask, LE);
  dv.setUint16(base + 8, value.nPulses, LE);
  dv.setUint16(base + 10, value.nGates, LE);
  dv.setUint8(base + 12, value.clutterFilter);
  dv.setUint8(base + 13, value.dealiasMode);
  dv.setUint8(base + 14, value.sweepMode);
  dv.setUint8(base + 15, value.estimator);
  dv.setUint8(base + 16, value.rfiFilter);
  dv.setUint8(base + 17, value.rangeDealiasMode);
  dv.setUint8(base + 18, value.prfRatioNum);
  dv.setUint8(base + 19, value.prfRatioDen);
  dv.setFloat32(base + 20, value.startRangeM, LE);
  dv.setFloat32(base + 24, value.gateSpacingM, LE);
  dv.setFloat32(base + 28, value.prfHz, LE);
  dv.setFloat32(base + 32, value.sqiThreshold, LE);
  dv.setFloat32(base + 36, value.sigThreshold, LE);
  dv.setFloat32(base + 40, value.ccorThreshold, LE);
  dv.setFloat32(base + 44, value.logThreshold, LE);
  dv.setFloat32(base + 48, value.clutterWidthMs, LE);
  dv.setFloat32(base + 52, value.radarConstantDb, LE);
  dv.setFloat32(base + 56, value.noiseFloorDbm, LE);
  dv.setFloat32(base + 60, value.receiverGainDb, LE);
  dv.setFloat32(base + 64, value.zdrOffsetDb, LE);
  dv.setFloat32(base + 68, value.phidpOffsetDeg, LE);
  dv.setFloat32(base + 72, value.antennaIsolationDb, LE);
  dv.setFloat32(base + 76, value.wavelengthM, LE);
  dv.setUint8(base + 80, value.polarizationMode);
  dv.setUint8(base + 81, value.transmitterType);
  dv.setUint16(base + 82, value.burstWindowBins, LE);
  dv.setUint8(base + 84, value.pulseWidthIdx);
  dv.setUint8(base + 85, value.cellMode);
  dv.setUint32(base + 86, value.prfDiv, LE);
  dv.setFloat32(base + 90, value.triggerDelay0, LE);
  dv.setFloat32(base + 94, value.triggerDelay1, LE);
  dv.setFloat32(base + 98, value.triggerDelay2, LE);
  dv.setFloat32(base + 102, value.triggerDelay3, LE);
  dv.setFloat32(base + 106, value.triggerWidth0, LE);
  dv.setFloat32(base + 110, value.triggerWidth1, LE);
  dv.setFloat32(base + 114, value.triggerWidth2, LE);
  dv.setFloat32(base + 118, value.triggerWidth3, LE);
  return dv;
}

/**
 * Mandato del plano de control. Se responde siempre con un config_ack.
 */
export interface Control {
  /** Se devuelve tal cual en el config_ack. */
  seq: number;
  /** Ver la enumeración de mandatos. */
  command: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
  /** Relleno explícito; vale 0. */
  pad1: number;
}

export const CONTROL_SIZE = 8;

export const CONTROL_OFFSETS = {
  seq: 0,
  command: 4,
  pad0: 5,
  pad1: 6,
} as const;

export function decodeControl(view: DataView, base = 0): Control {
  return {
    seq: view.getUint32(base + 0, LE),
    command: view.getUint8(base + 4),
    pad0: view.getUint8(base + 5),
    pad1: view.getUint16(base + 6, LE),
  };
}

export function encodeControl(value: Control, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(CONTROL_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setUint8(base + 4, value.command);
  dv.setUint8(base + 5, value.pad0);
  dv.setUint16(base + 6, value.pad1, LE);
  return dv;
}

/**
 * Arranca el autotest de enlace. Obligatorio en cada reconexión del RCP.
 */
export interface SelftestRequest {
  /** Se devuelve tal cual en el selftest_result. */
  seq: number;
  /** Valor arbitrario que el DSP devuelve, para casar respuesta con petición. */
  nonce: number;
}

export const SELFTEST_REQUEST_SIZE = 8;

export const SELFTEST_REQUEST_OFFSETS = {
  seq: 0,
  nonce: 4,
} as const;

export function decodeSelftestRequest(view: DataView, base = 0): SelftestRequest {
  return {
    seq: view.getUint32(base + 0, LE),
    nonce: view.getUint32(base + 4, LE),
  };
}

export function encodeSelftestRequest(value: SelftestRequest, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(SELFTEST_REQUEST_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setUint32(base + 4, value.nonce, LE);
  return dv;
}

/**
 * Pide una traza de espectro de FI (spectrum_frame) con canal y
 * promediado elegidos (issue #1 ítem 7, mapeo RCP entrada 6). Alternativa
 * parametrizada a `command::request_spectrum` (control, sin parámetros), que
 * sigue existiendo tal cual con su comportamiento de hoy: canal RX_0, un
 * periodograma por mandato, sin promediar entre mandatos sucesivos.
 */
export interface RequestSpectrum {
  /** Se devuelve como spectrum_frame.seq. */
  seq: number;
  /** Canal físico a muestrear — bit único de drx_dsp::channel (RX_0/RX_1/RX_2/RX_3/TX_BURST_0). Sin ese canal en el radial vigente, no hay traza que mandar, igual que hoy con RX_0 fijo. */
  channel: number;
  /** Radiales sucesivos de ese canal a acumular en potencia (nunca en dB, ver docs/algorithms/analizador-espectro-fi.md) antes de responder con un único spectrum_frame. 0 o 1: un solo radial, mismo comportamiento que command::request_spectrum. Más promedios reduce el ruido de la traza a costa de la latencia de refresco. */
  nAverages: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
}

export const REQUEST_SPECTRUM_SIZE = 8;

export const REQUEST_SPECTRUM_OFFSETS = {
  seq: 0,
  channel: 4,
  nAverages: 5,
  pad0: 6,
} as const;

export function decodeRequestSpectrum(view: DataView, base = 0): RequestSpectrum {
  return {
    seq: view.getUint32(base + 0, LE),
    channel: view.getUint8(base + 4),
    nAverages: view.getUint8(base + 5),
    pad0: view.getUint16(base + 6, LE),
  };
}

export function encodeRequestSpectrum(value: RequestSpectrum, view?: DataView, base = 0): DataView {
  const dv = view ?? new DataView(new ArrayBuffer(REQUEST_SPECTRUM_SIZE));
  dv.setUint32(base + 0, value.seq, LE);
  dv.setUint8(base + 4, value.channel);
  dv.setUint8(base + 5, value.nAverages);
  dv.setUint16(base + 6, value.pad0, LE);
  return dv;
}

/**
 * Códigos de rechazo del plano de control.
 */
export const Error = {
  /** Aceptado. */
  OK: 0,
  /** version_major desconocido. */
  UNSUPPORTED_VERSION: 1,
  /** msg_type desconocido. */
  UNKNOWN_MESSAGE: 2,
  /** payload_len no cuadra con el mensaje. */
  BAD_LENGTH: 3,
  /** Llegó un config estando en marcha. */
  NOT_IN_SETUP_PHASE: 4,
  /** Llegó un arranque antes de la primera configuración. */
  NOT_CONFIGURED: 5,
  /** Se pidió un momento que esta compilación no produce. */
  MOMENT_UNSUPPORTED: 6,
  /** Se pidió un modo de dealiasing no disponible. */
  DEALIAS_UNSUPPORTED: 7,
  /** Se pidió un estimador no disponible. */
  ESTIMATOR_UNSUPPORTED: 8,
  /** Un umbral cae fuera de su rango admisible. */
  THRESHOLD_OUT_OF_RANGE: 9,
  /** PRF y extensión de rango incompatibles; ver D-09 del DRx. */
  PRF_RANGE_ILLEGAL: 10,
  /** n_gates por encima de max_gates. */
  GATE_COUNT_ILLEGAL: 11,
  /** El autotest de enlace no pasó. */
  SELFTEST_FAILED: 12,
  /** No hay enlace con el DRx; no se puede arrancar. */
  DRX_LINK_DOWN: 13,
} as const;

/**
 * Vocabulario canónico de momentos, común a los planes del DSP y del RCP.
 * Reconcilia el nombrado heredado de Vesta (dBZ/dBT) con el del RCP (UZ/CZ).
 */
export const MomentKind = {
  /** Reflectividad sin corregir, dBZ. */
  UZ: 0,
  /** Reflectividad corregida, dBZ. */
  CZ: 1,
  /** Velocidad radial media, m/s. */
  V: 2,
  /** Ancho espectral, m/s. */
  W: 3,
  /** Reflectividad diferencial, dB. */
  ZDR: 4,
  /** Fase diferencial, grados. */
  PHIDP: 5,
  /** Fase diferencial específica, grados/km. */
  KDP: 6,
  /** Razón de despolarización lineal, dB. */
  LDR: 7,
  /** Coeficiente de correlación copolar, adimensional. */
  RHOHV: 8,
  /** Índice de calidad de señal, 0 a 1. */
  SQI: 9,
  /** Corrección de clutter aplicada, dB. */
  CCOR: 10,
  /** Señal sobre ruido, dB. */
  SIG: 11,
  /** Componente en fase cruda. */
  I: 12,
  /** Componente en cuadratura cruda. */
  Q: 13,
} as const;

/**
 * Banderas por radial. Un radial con problemas se MARCA, no se descarta.
 */
export const RayFlag = {
  /** Primer radial del barrido. */
  SWEEP_START: 1,
  /** Último radial del barrido. */
  SWEEP_END: 2,
  /** Primer radial del volumen. */
  VOLUME_START: 4,
  /** Último radial del volumen. Cierra el fichero Level-II. */
  VOLUME_END: 8,
  /** Alguna celda quedó censurada por umbral. */
  CENSORED: 16,
  /** El dealiasing no convergió en este radial. */
  DEALIAS_FAILED: 32,
  /** Se aplicó filtrado de clutter. */
  CLUTTER_FILTERED: 64,
  /** Primer radial con la configuración nueva. */
  FIRST_AFTER_CONFIG: 128,
} as const;

/**
 * Banderas por bloque de momento dentro de un radial.
 */
export const MomentFlag = {
  /** El bloque contiene celdas sin dato, codificadas como NaN. */
  HAS_MISSING: 1,
  /** El momento lleva correcciones de calibración aplicadas. */
  CORRECTED: 2,
  /** El momento se calculó tras el filtro de clutter. */
  FILTERED: 4,
} as const;

/**
 * Fases del DSP. Configurar y adquirir son pasos distintos.
 */
export const Phase = {
  /** Admite configuración; no emite momentos. */
  SETUP: 0,
  /** Emite momentos; rechaza configuración. */
  RUNNING: 1,
  /** Parado por fallo; sólo admite status y autotest. */
  FAULT: 2,
} as const;

/**
 * Mandatos del plano de control.
 */
export const Command = {
  /** Para la adquisición y vuelve a fase de configuración. */
  ENTER_SETUP: 0,
  /** Pasa a marcha con la configuración vigente. */
  START: 1,
  /** Para la adquisición sin perder la configuración. */
  STOP: 2,
  /** Pide un status inmediato. */
  REQUEST_STATUS: 3,
  /** Pide de vuelta la configuración vigente. */
  REQUEST_CONFIG: 4,
  /** Pide el mensaje de capacidades. */
  REQUEST_CAPABILITIES: 5,
  /** Pone a cero los contadores de telemetría. */
  RESET_COUNTERS: 6,
  /** Pide una traza de espectro de FI (spectrum_frame) oportunista sobre el flujo vivo. Sin ráfaga en curso no hay traza que mandar. */
  REQUEST_SPECTRUM: 7,
} as const;

/**
 * Modos de barrido. Los cinco primeros (0-4) son patrón de movimiento de
 * antena; los tres nuevos de v1.5 (5-7) son tipo de corte de rango/velocidad
 * (`docs/algorithms/procesamiento-de-rango.md` §"Modos de barrido / tipos de
 * corte"). RVP900 legacy los trata como un único "major mode"; aquí conviven en
 * el mismo campo por compatibilidad con ese inventario, sin que sean mutuamente
 * excluyentes en la práctica (un PPI puede correr en split-cut). Este campo es
 * metadato de paso: `crates/service::ray` lo copia de `config` a cada
 * `MomentRay` sin ramificar sobre él — el reparto real de PRF baja/alta ya lo
 * decide `scan_mode` del contrato `DRx↔DSP` (`contract/vendor/drx_dsp_v0_1.rs`),
 * y `crates/range::compose_split_cut` sólo compone los momentos ya estimados.
 */
export const SweepMode = {
  /** Azimut variable a elevación fija. */
  PPI: 0,
  /** Elevación variable a azimut fijo. */
  RHI: 1,
  /** Sector de azimut acotado. */
  SECTOR: 2,
  /** Antena parada en una posición. */
  POINT: 3,
  /** Movimiento gobernado por el operador. */
  MANUAL: 4,
  /** Dos barridos completos a la misma elevación, PRF baja y PRF alta, compuestos (`compose_split_cut`). */
  SPLIT_CUT: 5,
  /** Mismo reparto PRF baja/alta que split cut, alternando bloques de pulsos dentro de un solo barrido. */
  BATCH_CUT: 6,
  /** Un único barrido a PRF alta; reflectividad y velocidad de la misma serie. */
  DOPPLER_CUT: 7,
} as const;

/**
 * Modos de extensión del intervalo de velocidad no ambigua.
 */
export const DealiasMode = {
  /** PRF único; Nyquist sin extender. */
  NONE: 0,
  /** PRF alternante por radial. */
  DUAL_PRF: 1,
  /** Periodo escalonado dentro del radial. */
  STAGGERED_PRT: 2,
} as const;

/**
 * Método de recuperación/detección de segundo trip
 * (`docs/algorithms/roadmap.md` §"Decisiones cerradas" ítem "`range_dealias`
 * sin SZ"). v0.2 lo declaraba con un solo bit booleano; v0.3 lo convierte en
 * enumeración para poder distinguir la vía SZ(8/64) (klistrón) de la vía
 * histórica de fase aleatoria (magnetrón) sin cambiar tamaño ni posición del
 * campo — `0`/`1` conservan el significado que ya tenían.
 */
export const RangeDealiasMode = {
  /** Sin recuperación de trip múltiple; sólo se procesa el primer trip. */
  NONE: 0,
  /** Detección y marcado cross-radial (`crates/service::ray`); recuperación real sólo en instalación magnetrón, vía la fase de burst aleatoria pulso a pulso (`lamula_range_dealias`). */
  RANDOM_PHASE: 1,
  /** Recuperación por codificación de fase SZ(8/64) (`docs/algorithms/sz-second-trip-recovery.md`, `crates/sz864`); exige transmisor con fase programable pulso a pulso (klistrón/TWT/estado sólido) y `capability_flag::sz864`. Sin cablear en `crates/service::ray` todavía. */
  SZ_8_64: 2,
} as const;

/**
 * Modo del segundo canal de recepción, cuando `n_rx_channels > 1`
 * (`docs/algorithms/roadmap.md` §"Decisiones cerradas"). Sin efecto con canal
 * único: no hay segundo canal con que elegir modo.
 */
export const PolarizationMode = {
  /** STAR: H y V transmitidos y recibidos a la vez. Da ZDR/ΦDP/KDP/ρHV; no LDR. */
  SIMULTANEOUS: 0,
  /** H/V alternante radial a radial. Da LDR; PRF efectiva por canal a la mitad. */
  ALTERNATING: 1,
} as const;

/**
 * Tipo de transmisor de la instalación (`docs/algorithms/roadmap.md`
 * §"Dos ejes de variabilidad del hardware", eje 1). Sólo estos dos valores: el
 * parque confirmado es magnetrón + klistrón, no hay TWT ni estado sólido
 * desplegado — añadir uno nuevo cuando exista, no antes.
 */
export const TransmitterType = {
  /** Oscilador libre: fase de pulso aleatoria (recuperación de segundo trip por fase aleatoria), corrección de fase por burst y AFC obligatorios. */
  MAGNETRON: 0,
  /** Amplificador coherente con excitador de fase programable pulso a pulso: recuperación de segundo trip por SZ(8/64) (`range_dealias_mode::SZ_8_64`), corrección de fase por burst y AFC opcionales. */
  KLYSTRON: 1,
} as const;

/**
 * Estimadores de momentos.
 */
export const Estimator = {
  /** Autocovarianza a retardo 1. Primario. */
  PULSE_PAIR: 0,
  /** FFT y ajuste espectral. Alternativo, más caro. */
  SPECTRAL: 1,
} as const;

/**
 * Filtros de eco fijo.
 */
export const ClutterFilter = {
  /** Sin filtrar. */
  NONE: 0,
  /** GMAP: ajuste gaussiano e interpolación del hueco. */
  GMAP: 1,
  /** Notch fijo en velocidad cero. */
  NOTCH: 2,
} as const;

/**
 * Codificación de los valores de un bloque de momento.
 */
export const DataType = {
  /** IEEE-754 de 32 bits. Único tipo en v0.1. */
  F32: 0,
  /** Reservado: entero de 16 bits con scale y offset. */
  I16_SCALED: 1,
} as const;

/**
 * Niveles de severidad, comunes a status y a los sucesos de BITE.
 */
export const Severity = {
  /** Informativo; no degrada el servicio. */
  INFO: 0,
  /** Degradación que no impide operar. */
  WARNING: 1,
  /** Fallo que impide producir momentos válidos. */
  FAULT: 2,
  /** La configuración vigente es inconsistente. */
  CONFIG_ERROR: 3,
} as const;

/**
 * Modos de proceso que una compilación del DSP puede ofrecer.
 */
export const CapabilityFlag = {
  /** Estimadores polarimétricos disponibles. */
  DUAL_POL: 1,
  /** Estimador espectral disponible. */
  SPECTRAL_ESTIMATOR: 2,
  /** Dealiasing dual-PRF disponible. */
  DUAL_PRF: 4,
  /** Dealiasing por PRT escalonado disponible. */
  STAGGERED_PRT: 8,
  /** Recuperación/detección de trip múltiple por fase aleatoria (magnetrón) disponible. Ver `range_dealias_mode::random_phase`. */
  RANGE_DEALIAS: 16,
  /** Filtrado de interferencia de banda estrecha disponible. */
  RFI_FILTER: 32,
  /** Analizador de espectro de FI disponible. */
  SPECTRUM_FEED: 64,
  /** Volcado de series temporales crudas disponible. */
  IQ_ARCHIVE: 128,
  /** Recuperación de trip múltiple por codificación de fase SZ(8/64) disponible (exige klistrón/TWT/estado sólido con fase programable). Ver `range_dealias_mode::sz_8_64`. */
  SZ864: 256,
} as const;

/**
 * Banderas de la cabecera común, válidas en cualquier mensaje.
 *
 * `simulated_source` es procedencia, no capacidad: dice que los datos de ESTA
 * trama no vienen de hardware real. Va en la cabecera y no en `capabilities`
 * a propósito, por tres razones: llega con cada trama, incluido cada
 * `moment_ray`, así que el codificador de Level-II del RCP puede decidir sobre
 * el dato que tiene en la mano en vez de recordar un mensaje anterior; no se
 * pierde si el RCP se reengancha a mitad de adquisición; y no obliga a una
 * petición previa. Publicar dato simulado como si fuera observación es el fallo
 * que no se detecta hasta que ya está archivado con marca de tiempo absoluta.
 */
export const HeaderFlag = {
  /** La fuente de datos es un simulador, no el DRx real. */
  SIMULATED_SOURCE: 1,
} as const;

/**
 * Catálogo de fallos del DSP.
 */
export const BiteFlag = {
  /** Se perdieron radiales del DRx. */
  INGEST_DROP: 1,
  /** La cola de ingesta se desbordó. */
  QUEUE_OVERFLOW: 2,
  /** Enlace con el DRx caído. */
  DRX_LINK_DOWN: 4,
  /** El DRx rechazó una configuración. */
  DRX_CONFIG_REJECTED: 8,
  /** El periodo de disparo medido se apartó del mandado. */
  TRIGGER_DRIFT: 16,
  /** El suelo de ruido se apartó del calibrado. */
  NOISE_FLOOR_DRIFT: 32,
  /** La estimación de momentos no siguió el ritmo de radiales. */
  MOMENT_OVERRUN: 64,
  /** La calibración lleva demasiado sin verificarse. */
  CALIBRATION_STALE: 128,
  /** Enlace con el RCP caído. */
  RCP_LINK_DOWN: 256,
  /** Sin espacio para el archivo de I/Q crudo. */
  ARCHIVE_FULL: 512,
} as const;
