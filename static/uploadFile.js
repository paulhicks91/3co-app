async function getFiles() {
    const file_input = document.getElementById("fileUpload");

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

async function uploadFile() {
    document.getElementById('players').innerHTML = "";
    let playerTxt;
    let filename;

    const profileRegex = new RegExp('^[a-f0-9]{24}-[0-9]$');
    const files = getFiles();

    if (files === null) {
        return;
    }

    const profileDict = {};

    for (const file of files.files) {
        if (!('name' in file) || file.name.endsWith('.zip') || file.name.endsWith('.json')) {
            continue;
        }

        if (file.name.endsWith('.zip')) {
            const entries = await unzipArchive(file);

            if (entries.length === 0) {
                continue;
            }

            let totalPlayers = 0;
            for (const entry in entries) {
                filename = new TextDecoder().decode(entry.rawFilename);

                if (filename.endsWith('.json')) {
                    const parsedJSON = await parseMatchJSON(entry);

                    if (!('playerMatchStats' in parsedJSON)) {
                        continue;
                    }

                    const players = parsedJSON.playerMatchStats;

                    for (const player of players) {
                        if (!(('playerId' in player) && ('nickname' in player))) {
                            continue;
                        }

                        if (profileRegex.test(player.playerId)) {
                            const profile = player.playerId + ' ' + player.nickname;

                            profileDict[profile] = profileDict[profile] ? profileDict[profile] + 1 : 1;

                            totalPlayers += 1;
                        }
                    }
                }

                if (totalPlayers >= 300) {
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
        document.getElementById("status").innerHTML = "OOOF! IT LOOKS LIKE THAT WASN'T A PROPER FILE<br>PLEASE SELECT 1 OR MORE NEW FILE(S)";
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


async function parseMatchJSON(file, is_zipped) {
    let text = ""
    if (is_zipped === true) {
        text = await file.getData(new zip.TextWriter());
    } else {
        const reader = new FileReader();
        reader.onload = function () {
            text = reader.result;
        };
        reader.readAsText(file);
    }

    const parsedJSON = JSON.parse(text);

    if ('playerMatchStats' in parsedJSON) {
        return parsedJSON.playerMatchStats;
    }

    return [];
}


async function extractPlayers(playerStats) {

}