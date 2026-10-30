# Pubblicazione guidata: sorgenti privati e due download

## Repository privato
Crea su GitHub un repository **DocFlow**, visibilità **Private**, senza README automatico. Carica il contenuto di questa cartella Repository (oppure della cartella estratta da DocFlow_GitHub.zip), comprese `.github` e `.gitignore`. Non caricare il bundle DocFlow.app o le cartelle temporanee di build nell'elenco dei sorgenti.

## Verifica Windows
Dopo il caricamento, nella scheda **Actions** apri **Verifica e prepara demo Windows**, poi **Run workflow**. Il workflow è manuale: non parte automaticamente all'upload. Se Actions chiede un'abilitazione o non è disponibile, si può effettuare la prova su un PC Windows. Un esito positivo attesta il test del motore e del pacchetto, non una verifica visiva completa dell'interfaccia su tutti i browser.

È inoltre opportuna la prova con doppio clic del comando su un PC Windows: estrazione completa, avvio della pagina, lotto fittizio, approvazione, ZIP scaricato e chiusura.

## Release privata
Crea una pre-release con tag `v0.1.0-demo`, titolo **DocFlow — Demo Mac e Windows**. Allegati:

- `DocFlow_MAC.zip`: solo Mac Apple Silicon.
- `DocFlow_WINDOWS_x64.zip`: Windows 10/11 x64 Intel/AMD.

La release eredita la visibilità privata del repository. Non serve rendere pubblico il codice per distribuire i pacchetti alle persone autorizzate. Indicare nelle note se la prova Windows è ancora da completare.

## Video dimostrativi pubblici, in seguito
Conserva i sorgenti e le release in questi repository privati. Quando vorrai rendere visibile il lavoro, crea uno spazio pubblico distinto che contenga soltanto descrizioni, immagini e video dimostrativi con dati fittizi. Non caricare HTML, sorgenti o pacchetti dell'app in quello spazio se vuoi mostrare solo il funzionamento.

Un repository pubblico dedicato ai video oppure un servizio di video hosting può essere collegato dal profilo GitHub. Un collegamento a un video salvato in un repository privato non lo rende pubblico. Questa guida non pubblica né modifica la visibilità di alcun repository.
