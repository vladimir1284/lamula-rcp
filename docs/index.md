# LAMULA RCP

Radar Control Processor & Operator MMI — sucesor en casa de Ravis 1.3 + RCP + Rainbow para un
radar meteorológico Gematronik, sin dependencia del vendor original.

El RCP controla el radar, ingiere momentos pre-calculados del DSP/DRX, archiva la observación
volumétrica como NEXRAD Level-II, y alimenta esa base data a ORPG mediante una emulación
completa de RDA WSR-88D (ICD 2620002). ORPG genera todos los productos; el RCP no genera
ninguno.

El plan de proyecto completo (objetivos, arquitectura, stack, fases, riesgos, equipo) vive en
[Project Plan](referencia/project-plan.md). Esta documentación traduce ese plan a
decisiones y pendientes accionables para el agente de desarrollo, siguiendo la misma convención
que `radar_emulator` (mismo equipo, proyecto hermano: la planta emulada del radar contra la que
este RCP se valida antes de comisionar sobre hardware real).

Empieza por [Contexto y alcance](alcance/contexto.md).

!!! danger "Repo recién creado"
    Solo existe el scaffold de documentación. La Fase 0 (congelar los cuatro contratos, spikes
    de Modbus/UDP contra `radar_emulator`) todavía no se ha ejecutado. Ver
    [Fases](implementacion/fases.md).
