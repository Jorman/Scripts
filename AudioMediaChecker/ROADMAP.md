# ROADMAP & PIANO DI IMPLEMENTAZIONE AUDIO MEDIA CHECKER

Documento di tracciamento e guida operativa per lo sviluppo, l'ottimizzazione e il refactoring di `AudioMediaChecker.py`.

---

## 🛡️ PROTOCOLLO OPERATIVO E REGOLE FERREE (AMBIENTE DI PRODUZIONE)

Poiché lo script opera in ambiente di produzione ed effettua modifiche dirette sui metadati dei file multimediali, ogni ciclo di modifica deve attenersi tassativamente alle seguenti regole:

1. **Integrità Assoluta dei File Multimediali di Test:**
   * I file multimediali reali forniti per i test **NON DEVONO MAI ESSERE MODIFICATI O SOVRASCRITTI**.
   * Qualsiasi test funzionale deve essere condotto:
     * In modalità `--dry-run` (simulazione sicura), oppure
     * Creando una copia temporanea di backup/sandbox in directory isolata (es. scratch/tmp), su cui eseguire il test di scrittura, verificando il risultato ed eliminando la copia al termine.
2. **Test Obbligatorio su File Reali a Ogni Step:**
   * Nessuna modifica viene considerata conclusa senza aver prima richiesto file reali di test all'utente e aver convalidato l'output.
3. **Nessun Commit senza Esito Positivo al 100%:**
   * Nessun commit o push su Git verrà effettuato finché i test non confermano la totale assenza di regressioni e il corretto funzionamento della specifica modifica.
4. **Sviluppo Modulare e Incrementale:**
   * Si affronta un singolo task alla volta. Non si accorpano più modifiche complesse nello stesso ciclo.

---

## 📋 INDICE DEI TASK E STATO DI AVANZAMENTO

| ID | Titolo | Categoria | Priorità | Stato |
|:---|:---|:---|:---:|:---:|
| **TASK-01** | Caching Modello Whisper tra File Multipli e Cleanup Risorse | Bugfix / Performance | Alta | ✅ Completato |
| **TASK-02** | Riformulazione Campionamento (4 Campioni Vocali Validi + Quorum) e Gestione Muti | Algoritmo / Precisione | Alta | Pianificato |
| **TASK-03** | Gestione Segnali di Interruzione Pulita (Graceful Shutdown) | Stabilità / OS | Media | Pianificato |
| **TASK-04** | Ottimizzazione Rilevamento Lingua vs Trascrizione Completa | Performance | Media | Pianificato |
| **TASK-05** | Supporto Variabili d'Ambiente (Docker-Friendly Configuration) | Feature | Bassa | Pianificato |
| **TASK-06** | Pipeline Parallela Estrazione FFmpeg / Inferenza Whisper | Performance / Concorrenza | Media | Pianificato |
| **BACKLOG-01**| Supporto `--json` per Cartelle Multiple | Feature / Architettura | - | In Sospeso |
| **BACKLOG-02**| Studio Disallineamento Indici `ffprobe` vs `mkvpropedit` | Analisi Edge Case | - | In Sospeso |
| **BACKLOG-04**| Sistema di Notifiche Webhook Post-Elaborazione | Feature | - | In Sospeso |

---

## DETTAGLIO DEI TASK DI SVILUPPO

---

### TASK-01: Caching Modello Whisper tra File Multipli e Cleanup Risorse

* **Riferimento analisi:** Punto 1.1
* **Stato:** ✅ Completato

#### 1. Descrizione del Problema
Nel ciclo `main()`, per ciascun file individuato nella cartella viene istanziata una nuova classe `AudioMediaChecker`. Sebbene la classe disponga internamente di un meccanismo lazy per inizializzare Whisper (`self._whisper`), tale istanza viene distrutta al termine di ogni file.
Se l'utente esegue lo script su una cartella con decine o centinaia di file, il modello Whisper (da centinaia di megabyte a svariati gigabyte di pesi) viene allocato, caricato da disco e deallocato **da zero per ogni singolo file**.
Questo causa:
* Spreco enorme di tempo (da 5 a 30 secondi di overhead per file).
* Continuo riempimento e svuotamento di RAM e VRAM GPU.
* Rischio di frammentazione della memoria GPU su lunghe sessioni.
* Nessuno scaricamento esplicito (cleanup) della memoria prima della chiusura dello script.

#### 2. Come Risolvere il Problema
* **Condivisione dell'istanza del modello:** Il modello Whisper deve essere istanziato una sola volta (al primo file che richiede effettivamente un'analisi) e riutilizzato per tutti i file successivi della sessione.
* **Separazione delle responsabilità:** `AudioMediaChecker` deve poter ricevere un'istanza già esistente del modello Whisper oppure demandare la gestione del modello a un gestore di sessione / singleton.
* **Cleanup Esplicito all'Uscita:** Prima dell'uscita del programma (sia naturale che per interruzione o eccezione), rilasciare esplicitamente l'oggetto `WhisperModel`, invocare la garbage collection di Python (`gc.collect()`) e, in caso di GPU, svuotare la cache VRAM (`torch.cuda.empty_cache()` se disponibile).

#### 3. Step Operativi per la Risoluzione
1. Modificare il costruttore di `AudioMediaChecker` per accettare un parametro opzionale `whisper_model=None`.
2. Se il modello viene passato dall'esterno, riutilizzarlo direttamente senza richiamare `_lazy_load_whisper`.
3. Nel `main()`, gestire il riferimento al modello a livello di ciclo globale sui file:
   * Al primo file analizzato che necessita di rilevamento vocale, istanziare il modello e salvarne il riferimento.
   * Passare il modello condiviso a tutti i file successivi.
4. Creare una funzione di cleanup esplicita `unload_whisper_model(model)`:
   * Cancellazione del riferimento (`del model`).
   * Esecuzione di `gc.collect()`.
   * Rilascio della memoria CUDA se attivo `--gpu`.
5. Integrare la chiamata di cleanup nel blocco `finally` del `main()`.

#### 4. Test di Analisi e Criteri di Verifica
* **Test su file reali (Cartella con almeno 2-3 file):**
  * Eseguire lo script in modalità `--dry-run` su una cartella di test contenente almeno 3 file video.
  * Verificare dai log che il messaggio di caricamento del modello (`Loading Whisper model...`) compaia **una sola volta** all'inizio e non per ciascun file.
  * Verificare con `nvidia-smi` (su GPU) o monitoraggio RAM (su CPU) che la memoria rimanga stabile e venga liberata completamente al termine dello script.

---

### TASK-02: Riformulazione Media Ponderata e Gestione Audio Muti / Non Vocali

* **Riferimento analisi:** Punti 1.2 e 2.2
* **Stato:** Pianificato

#### 1. Descrizione del Problema
L'attuale calcolo della media ponderata presenta un vizio logico:
`weighted_average = total_confidence_lingua / total_detections`
Se si effettuano 4 campionamenti:
* Campione 1 (10% del film): Sigla musicale iniziale, Whisper non sente parlato e assegna casualmente una lingua secondaria con confidenza 0.10.
* Campione 2 (35% del film): Parlato italiano chiaro, confidenza 0.98.
* Campione 3 (60% del film): Parlato italiano chiaro, confidenza 0.97.
* Campione 4 (85% del film): Parlato italiano chiaro, confidenza 0.95.
Il totale per l'italiano è `2.90`. Dividendo per `4` campionamenti, la media risulta `72.5%`. Se la musica fosse durata anche per il secondo campione, la media scenderebbe a `48.7%`, fallendo la soglia del 65% nonostante l'italiano sia chiarissimo in tutto il parlato!

Inoltre, nei **film muti** o nelle tracce audio puramente di effetti/colonna sonora (senza dialoghi), Whisper tenta comunque di indovinare una lingua sul rumore di fondo. Lo script fa 10 tentativi esaustivi e casuali da 30 a 90 secondi, sprecando minuti di calcolo inutilmente senza mai raggiungere la soglia.

#### 2. Come Risolvere il Problema
* **Garanzia di 4 Campionature Vocali Valide:**
  * L'analisi di una traccia deve raccogliere sempre e comunque **4 campioni vocali validi** (cioè segmenti in cui Whisper rileva effettivamente presenza di parlato umano).
  * Le posizioni fisse iniziali (10%, 35%, 60%, 85%) sono ideate per scavalcare sigle e titoli di coda; tuttavia, se un campione cade su una scena senza dialoghi (es. `no_speech_prob > 0.65` o silenzio), tale campione viene scartato e lo script seleziona immediatamente un **nuovo punto percentuale** da campionare finché non raggiunge la quota di 4 campioni validi.
* **Protezione e Riconoscimento Tracce Senza Voce / Film Muti:**
  * Per evitare loop infiniti nei film muti o nelle tracce audio puramente musicali/effetti sonori, si imposta un limite massimo di campioni testabili (es. 8–10 tentativi di campionamento a posizioni diverse).
  * Se anche dopo aver esplorato 8-10 punti della traccia tutti i segmenti risultano privi di parlato (`no_speech_prob` costantemente alto), la traccia viene classificata con certezza come *"Traccia Priva di Parlato / Non Vocale"*.
  * Viene emesso un log esplicito, si evita la cascata dei 9 tentativi successivi a vuoto e la traccia non viene alterata (o associata al codice ISO 639-2 `zxx` / `und`).
* **Principio del Quorum sui 4 Campioni Validi:**
  * Una volta ottenuti i 4 campioni vocali validi, si applica la logica del quorum:
    * La lingua dominante deve essere confermata nella maggioranza dei campioni validi (almeno 3 su 4, pari al 75%, o minimo 50%+1).
    * La media delle confidenze della lingua vincente calcolata esclusivamente sui campioni in cui è comparsa deve essere `>= --confidence` (default 65%).
    * In questo modo, l'eventuale presenza di una singola parola spuria in altra lingua o rumore residuo non inficia il risultato corretto.

#### 3. Step Operativi per la Risoluzione
1. In `detect_language()`, estrarre e restituire sia `detected_language`, sia `confidence`, sia `info.no_speech_prob`.
2. Nella logica di campionamento:
   * Mantenere una lista di campioni vocali validi `valid_samples = []`.
   * Partire dai punti base (10%, 35%, 60%, 85%).
   * Se un punto presenta `no_speech_prob > 0.65`, loggarlo (`Campione al X% privo di parlato, selezione nuova posizione...`) e generare una nuova coordinata temporale non ancora esplorata.
   * Porre un tetto massimo di esplorazione (max 8 campionamenti totali per traccia). Se si esaurisce il tetto senza raggiungere 4 campioni validi:
     * Se ci sono 0 campioni vocali: traccia dichiarata muta/non vocale.
     * Se ci sono 1-3 campioni vocali: valutare quorum proporzionale oppure procedere con cautela al retry dinamico.
3. Se si ottengono i 4 campioni vocali validi:
   * Calcolare le occorrenze di ciascuna lingua e la relativa media di confidenza.
   * Applicare la verifica del quorum (lingua vincente presente in ≥3 campioni su 4 con media ≥ soglia).
   * Se il quorum è raggiunto, validazione immediata al primo tentativo! Altrimenti, avviare il retry guidato.

#### 4. Test di Analisi e Criteri di Verifica
* **Test su file reale con colonna sonora/intro lunga o pause mute:**
  * Verificare dai log che se un campione cade nel silenzio, viene scartato e sostituito da un punto alternativo fino ad avere esattamente 4 campioni vocali validi.
* **Test su file muto o traccia solo musica/effetti:**
  * Verificare che dopo il numero massimo di tentativi di ricerca (es. 8) lo script dichiari la traccia non vocale e non avvii i 10 tentativi di retry a vuoto.
  * Eseguire esclusivamente con `--dry-run`.

---

### TASK-03: Gestione Segnali di Interruzione Pulita (Graceful Shutdown)

* **Riferimento analisi:** Punto 1.4
* **Stato:** Pianificato

#### 1. Descrizione del Problema
Nel codice esiste il flag `self.interrupted`, ma non c'è alcun gestore per `SIGINT` (Ctrl+C da terminale) o `SIGTERM` (richiesta di arresto da parte di Docker/Kubernetes).
Se l'utente ferma il container o preme Ctrl+C:
* Lo script viene abbattuto immediatamente.
* Se era in corso un'operazione di `mkvpropedit`, il file MKV potrebbe rimanere in uno stato incerto o corrotto.
* Le risorse di memoria (VRAM/RAM) e i file temporanei non vengono ripuliti.

#### 2. Come Risolvere il Problema
* Configurare un gestore di segnali centralizzato per `signal.SIGINT` e `signal.SIGTERM`.
* Alla ricezione del segnale:
  * Impostare un flag globale di interruzione.
  * Se un comando atomico su un file è in esecuzione, consentirgli di completare la singola scrittura prima di arrestarsi.
  * Interrompere il ciclo sui file successivi.
  * Invocare la routine di cleanup delle risorse (scaricamento modello).
  * Uscire con codice di terminazione standard (es. 130 per SIGINT).

#### 3. Step Operativi per la Risoluzione
1. Importare `signal`.
2. Definire un gestore `_signal_handler(signum, frame)` nel `main`.
3. Collegare `signal.signal(signal.SIGINT, handler)` e `signal.signal(signal.SIGTERM, handler)`.
4. Nel ciclo dei file, verificare il flag all'inizio di ogni iterazione e tra l'analisi e la scrittura.
5. In caso di interruzione, loggare `Arresto richiesto dall'utente/sistema, chiusura pulita in corso...`, eseguire il cleanup ed uscire.

#### 4. Test di Analisi e Criteri di Verifica
* Lanciare l'elaborazione di una cartella con più file in `--dry-run` e premere Ctrl+C durante l'analisi di un file: verificare che lo script intercetti il segnale, non avvii i file successivi, scarichi il modello ed esca in modo controllato.

---

### TASK-04: Ottimizzazione Rilevamento Lingua vs Trascrizione Completa

* **Riferimento analisi:** Punto 2.1
* **Stato:** Pianificato

#### 1. Descrizione del Problema
Attualmente la funzione `detect_language` chiama:
`segments, info = model.transcribe(audio_file, language=None, beam_size=5)`
`transcribe` esegue sia la classificazione dell'encoder per la lingua, sia la decodifica autoregressiva dell'intero testo parola per parola con fascio di ricerca (`beam_size=5`).
Poiché il testo trascritto non viene utilizzato per il tagging, generare parole e token per 30-90 secondi di audio per ogni campionamento causa un sovraccarico computazionale inutile, allungando i tempi di esecuzione di oltre il 300%.

#### 2. Come Risolvere il Problema
* `faster-whisper` include internamente la procedura ottimizzata di identificazione della lingua eseguita solo attraverso l'encoder audio, senza dover decodificare il testo.
* In alternativa, se si utilizza `transcribe`, disattivare il beam search (`beam_size=1`), limitare il decoding o richiamare `model.model.detect_language` sul tensore audio.
* In modalità `--verbose`, se l'utente desidera vedere il testo di esempio, si può mantenere la decodifica; altrimenti in modalità normale e `--json` deve essere eseguita esclusivamente la classificazione linguistica rapida.

#### 3. Step Operativi per la Risoluzione
1. Isolare la chiamata di language detection pura usando le feature native di `faster-whisper`.
2. Condizionare la decodifica completa del testo solo se il flag `--verbose` è attivo.
3. Misurare il tempo medio per singolo campione (30s) prima e dopo la modifica.

#### 4. Test di Analisi e Criteri di Verifica
* Eseguire l'analisi dello stesso file reale in `--dry-run` misurando i tempi di esecuzione.
* Verificare che la lingua rilevata e il punteggio di probabilità siano identici, con un tempo di calcolo marcatamente inferiore.

---

### TASK-05: Supporto Variabili d'Ambiente (Docker-Friendly)

* **Riferimento analisi:** Punto 3.3
* **Stato:** Pianificato

#### 1. Descrizione del Problema
Nei container Docker e negli stack Docker Compose, passare argomenti CLI lunghi è meno flessibile rispetto all'utilizzo di variabili d'ambiente (`environment:` nel compose o file `.env`).

#### 2. Come Risolvere il Problema
* Permettere ad `argparse` di prendere i valori predefiniti dalle variabili d'ambiente di sistema (es. `AMC_MODEL`, `AMC_CONFIDENCE`, `AMC_FORCE_LANGUAGE`, `AMC_CHECK_ALL_TRACKS`, `AMC_DRY_RUN`, `AMC_GPU`).
* Se un parametro viene passato sia via variabile che via riga di comando, l'argomento da riga di comando ha sempre la priorità.

#### 3. Step Operativi per la Risoluzione
1. Definire una mappatura delle variabili d'ambiente supportate con prefisso standard (es. `AMC_` per evitare collisioni).
2. Utilizzare `os.getenv` per impostare i `default` negli argomenti di `argparse`.
3. Documentare le variabili d'ambiente nel `README.md`.

#### 4. Test di Analisi e Criteri di Verifica
* Lanciare il comando impostando `AMC_CONFIDENCE=80` nell'ambiente senza passare `--confidence` via CLI e verificare che lo script usi la soglia 80.

---

### TASK-06: Pipeline Parallela Estrazione FFmpeg / Inferenza Whisper

* **Riferimento analisi:** Punto 2.3
* **Stato:** Pianificato

#### 1. Descrizione del Problema
L'attuale pipeline opera in modalità puramente sincrona e sequenziale:
1. FFmpeg si avvia, estrae il campione audio e scrive i dati in memoria (Whisper e la GPU/CPU restano in attesa inattivi).
2. Whisper riceve il campione ed esegue l'inferenza di rete neurale (FFmpeg e il disco restano completamente inattivi).
3. Completato il campione, si ripete il ciclo.
Nei film con tracce complesse o multiple, questo schema a blocchi raddoppia i tempi morti complessivi di calcolo e I/O.

#### 2. Come Risolvere il Problema
* Separare l'estrazione audio I/O (FFmpeg) dall'inferenza AI (Whisper) tramite un worker in background (asincrono o `ThreadPoolExecutor` / `Queue`):
  * Mentre Whisper elabora il campione corrente (es. Campione 1), un thread leggero in background avvia già FFmpeg per estrarre e preparare in memoria il campione successivo (Campione 2).
  * Quando Whisper ha terminato il campione 1, il campione 2 è già pronto in memoria (BytesIO), eliminando i tempi di attesa di I/O.
* Se un campione viene scartato per assenza di parlato, il prefetcher si adatta estraendo la posizione successiva.

#### 3. Step Operativi per la Risoluzione
1. Progettare un generatore/coda (`queue.Queue`) di pre-estrazione audio in streaming o threading.
2. Limitare il prefetch a un massimo di 1-2 campioni avanti per evitare consumo eccessivo di RAM.
3. Sincronizzare la coda con la logica di campionamento del TASK-02.

#### 4. Test di Analisi e Criteri di Verifica
* Misurare il tempo totale di analisi su un file reale di test con 2-3 tracce audio prima e dopo l'introduzione della pipeline asincrona.
* Verificare che l'uso della memoria resti costante e contenuto.

---

## ⏸️ BACKLOG E ELEMENTI IN SOSPESO (MONITORAGGIO)

---

### BACKLOG-01: Supporto `--json` su Cartelle Multiple
* **Riferimento analisi:** Punto 1.3
* **Stato:** In Sospeso (Backlog)
* **Motivazione:** Attualmente la modalità `--json` deve essere utilizzata esclusivamente su file singolo. Se richiamata con `--folder`, viene generato un flusso di array JSON multipli e disgiunti, privi del campo percorso file.
* **Azione futura:** Quando si affronterà questo punto, si implementerà un accumulatore globale nel `main` che raccoglie tutti i risultati e stampa un unico oggetto JSON strutturato:
  ```json
  [
    {
      "file": "/data/Movie1.mkv",
      "tracks": [{"track": 1, "language": "ita"}]
    }
  ]
  ```
  Fino ad allora, lo script emetterà un messaggio di errore chiaro se si tenta di usare `--json` con `--folder`.

---

### BACKLOG-02: Studio Disallineamento Indici `ffprobe` vs `mkvpropedit`
* **Riferimento analisi:** Punto 1.5
* **Stato:** In Sospeso (Backlog)
* **Motivazione:** È un caso limite complesso. Se un file MKV contiene allegati (es. font, cover art) o flussi speciali, l'indice `stream['index'] + 1` di ffprobe potrebbe non corrispondere esattamente al target track id di `mkvpropedit`.
* **Azione futura:** Valutare l'estrazione preventiva del Track UID o Track Number nativo di Matroska direttamente tramite `mkvmerge -J` o `ffprobe` con query specifica sui tag matroska, oppure tramite selettore di tipo `track:aN`.

---

### BACKLOG-04: Sistema di Notifiche Webhook Post-Elaborazione
* **Riferimento analisi:** Punto 3.5
* **Stato:** In Sospeso (Backlog)
* **Motivazione:** Possibilità di inviare payload a webhook Discord/Telegram o endpoint HTTP al termine della scansione. Registrato come idea per versioni future.
