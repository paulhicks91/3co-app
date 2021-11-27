async function getFiles() {
    const file_input = document.getElementById("myFile");
    if ('files' in file_input && !!file_input.files.length) {
        if (!file_input.files.length) {
            return []
        }
        return file_input.files;
    }
    let txt = "SELECT ONE OR MORE FILES.";
    if (file_input.value !== "") {
        txt = "THE FILES PROPERTY IS NOT SUPPORTED BY YOUR BROWSER!<br>";
        txt += "<br>THE PATH OF THE SELECTED FILE: " + file_input.value;
    }

    document.getElementById("status").innerHTML = txt;
    return null;
}

async function myFunction() {
    document.getElementById('players').innerHTML = "";
    let playerTxt;
    let filename;

    const profileRegex = new RegExp('^[a-f0-9]{24}-[0-9]$');
    const files = getFiles();

    if (files === null) {
        return;
    }

    const profileDict = {};
    for (let file of files.files) {
        if (!('name' in file)) {
            continue;
        }
        if (file.name.endsWith('.zip')) {
            const entries = await unzipArchive(file);
            if (entries.length === 0) {
                continue;
            }
            // get first entry content as text by using a TextWriter
            let totalPlayers = 0;
            for (const entry in entries) {
                filename = new TextDecoder().decode(entry.rawFilename);

                if (filename.endsWith('.json')) {
                    const players = await parseMatchJSON(entry);
                    for (const player of players) {
                        if (profileRegex.test(player.playerId)) {
                            const profile = player.playerId + ' ' + player.nickname;
                            profileDict[profile] = profileDict[profile] ? profileDict[profile] + 1 : 1;
                            totalPlayers += 1;
                        }
                    }
                }

                if (totalPlayers >= 200) {
                    break;
                }
            }
        }
    }


    if (Object.keys(profileDict).length !== 0) {
        playerTxt = "WHICH PROFILE IS YOURS?<br>";
        document.getElementById('fileLabel').innerHTML = "WRONG FILE? CLICK HERE";

        const profileArray = [];
        for (let playerProfile of Object.keys(profileDict)) {
            profileArray.push(String(profileDict[playerProfile]).padStart(2, '0') + ' ' + playerProfile);
        }
        profileArray.sort().reverse();
        for (let playerProfile of profileArray) {
            const splitProfileArr = playerProfile.split(' ');
            const profileName = splitProfileArr.slice(2,).join(' ');
            playerTxt += profileName.toUpperCase() + "<br>";
        }

        document.getElementById('players').innerHTML = playerTxt;
        document.getElementById("status").innerHTML = "";
    } else {
        document.getElementById("status").innerHTML = "OOOF! IT LOOKS LIKE THAT WASN'T A PROPER FILE<br>PLEASE SELECT (A) NEW FILE(S) TO TRY AGAIN";
        document.getElementById('fileLabel').innerHTML = "GIVE IT ANOTHER SHOT";
    }
}

async function unzipArchive(blob) {
    // create a BlobReader to read with a ZipReader the zip from a Blob object
    const reader = new zip.ZipReader(new zip.BlobReader(blob));
    // get all entries from the zip
    const entries = await reader.getEntries();
    // close the ZipReader
    await reader.close();

    return entries;
}


async function parseMatchJSON(file) {
    const text = await file.getData(new zip.TextWriter());
    const parsedJSON = JSON.parse(text);

    if ('playerMatchStats' in parsedJSON) {
        return parsedJSON.playerMatchStats;
    }

    return [];
}