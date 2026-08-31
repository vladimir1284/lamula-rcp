// GENERADO por tools/gen_contract.py a partir de
// contract/schema/dsp_rcp_v0_1.toml. NO EDITAR A MANO.
//
// Contrato DSP↔RCP v0.1 — lado MMI.
//
// Little-endian, empaquetado. Los enteros de 64 bits se exponen como
// bigint: no caben en el double de `number` sin perder enteros a partir
// de 2^53, y un timestamp en nanosegundos los supera de sobra.

/* eslint-disable */

export const MAGIC = 0x4C4D4453;
export const VERSION_MAJOR = 0;
export const VERSION_MINOR = 1;

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
  /** Reservado en v0.1; tiene que valer 0. */
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
  /** Relleno explícito; vale 0. */
  pad0: number;
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
}

export const STATUS_SIZE = 104;

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
  pad0: 52,
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
    pad0: view.getUint32(base + 52, LE),
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
  dv.setUint32(base + 52, value.pad0, LE);
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
  /** Relleno explícito; vale 0. */
  pad0: number;
}

export const CAPABILITIES_SIZE = 20;

export const CAPABILITIES_OFFSETS = {
  momentMask: 0,
  dealiasMask: 4,
  estimatorMask: 8,
  maxGates: 12,
  maxPulses: 16,
  nRxChannels: 18,
  pad0: 19,
} as const;

export function decodeCapabilities(view: DataView, base = 0): Capabilities {
  return {
    momentMask: view.getUint32(base + 0, LE),
    dealiasMask: view.getUint32(base + 4, LE),
    estimatorMask: view.getUint32(base + 8, LE),
    maxGates: view.getUint32(base + 12, LE),
    maxPulses: view.getUint16(base + 16, LE),
    nRxChannels: view.getUint8(base + 18),
    pad0: view.getUint8(base + 19),
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
  dv.setUint8(base + 19, value.pad0);
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
  /** Recuperación de trip múltiple: 0 no, 1 sí. */
  rangeDealias: number;
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
  /** Longitud de onda, metros. Escala la velocidad. */
  wavelengthM: number;
  /** Relleno explícito; vale 0. */
  pad0: number;
}

export const CONFIG_SIZE = 80;

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
  rangeDealias: 17,
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
  wavelengthM: 72,
  pad0: 76,
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
    rangeDealias: view.getUint8(base + 17),
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
    wavelengthM: view.getFloat32(base + 72, LE),
    pad0: view.getUint32(base + 76, LE),
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
  dv.setUint8(base + 17, value.rangeDealias);
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
  dv.setFloat32(base + 72, value.wavelengthM, LE);
  dv.setUint32(base + 76, value.pad0, LE);
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
} as const;

/**
 * Modos de barrido.
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
  /** Recuperación de trip múltiple disponible. */
  RANGE_DEALIAS: 16,
  /** Filtrado de interferencia de banda estrecha disponible. */
  RFI_FILTER: 32,
  /** Analizador de espectro de FI disponible. */
  SPECTRUM_FEED: 64,
  /** Volcado de series temporales crudas disponible. */
  IQ_ARCHIVE: 128,
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
