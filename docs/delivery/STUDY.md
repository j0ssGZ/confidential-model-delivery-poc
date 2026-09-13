# Ensayo personal después de la entrega

1. Leer la guía del evaluador y contar en voz alta la diferencia entre Layer 1,
   Layer 2 y Layer 3. Ubicar AES, privada/pública Ed25519, bundle, CDH y KBS.
2. En Notion: página principal → Presentación/Flujo → Layer 2 → Layer 3.
   Omitir inicialmente historial, hashes completos y comandos largos.
3. Seguir funciones: Producer → bundle → Consumer firmado → Consumer attested.
   Explicar por qué una firma inválida nunca debe provocar una petición AES.
4. Ejecutar tests y seguir REPRODUCTION.md en una copia/laboratorio propios.
   Crear parejas nuevas únicamente para nuevos bundles; conservar las originales.
5. En el Ubuntu existente, empezar inspeccionando y verificando sintético.
   No reinstalar componentes funcionales. Si KBS perdió recursos, reaprovisionar
   de forma controlada antes del E2E.
6. Explicar cada negativo usando su última etapa alcanzada y su código de salida.
   Poder explicar por qué un error de red o arranque no prueba denegación de policy.

No hace falta memorizar hashes ni grabar vídeo. El objetivo del ensayo es poder
recorrer código y demostrar decisiones con tus palabras. Esta lista sigue
pendiente hasta que tú la ejecutes; la evidencia previa no demuestra tu ensayo.
