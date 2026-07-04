export async function getGedcomFile() {

    return new Promise((resolve, reject) => {

        const request =
            indexedDB.open(
                "GenealogieDB",
                1
            );

        request.onsuccess = function(event){

            const db =
                event.target.result;

            const tx =
                db.transaction(
                    ["files"],
                    "readonly"
                );

            const store =
                tx.objectStore(
                    "files"
                );

            const getReq =
                store.get(
                    "gedcom"
                );

            getReq.onsuccess =
                () => resolve(
                    getReq.result
                );
        };
    });
}