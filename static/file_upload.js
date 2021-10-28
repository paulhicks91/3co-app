async function setup() {
    document.getElementById('players').innerHTML = "";
}

async function getFiles() {

    const file_input = document.getElementById("myFile");
    if ('files' in file_input && !!file_input.files.length) {
        if (!file_input.files.length) {
            return []
        }
        return file_input.files;
    }
    var txt = "";
    if (file_input.value === "") {
        txt = "SELECT ONE OR MORE FILES.";
    } else {
        txt = "THE FILES PROPERTY IS NOT SUPPORTED BY YOUR BROWSER!<br>";
        txt += "<br>THE PATH OF THE SELECTED FILE: " + file_input.value;
    }

    document.getElementById("status").innerHTML = txt;

    return null;
}

async function myFunction() {
    document.getElementById('players').innerHTML = "";
    var profileRegex = new RegExp('^[a-f0-9]{24}-[0-9]$')
    var x = document.getElementById("myFile");
    var txt = "";
    const files = getFiles();
    if (files === null) {

    }
    let playerTxt;
    if ('files' in x) {
        if (x.files.length == 0) {
            txt = "SELECT ONE OR MORE FILES.";
        } else {
            const profileDict = {};
            for (let file of x.files) {
                if ('name' in file) {
                    if (file.name.endsWith('.zip')) {
                        const entries = await unzipArchive(file);
                        if (entries.length) {
                            // get first entry content as text by using a TextWriter
                            for (var j = 0; j < Math.min(entries.length, 20); j++) {
                                const entry = entries[j];
                                filename = new TextDecoder().decode(entry.rawFilename);
                                console.log('name' in entry);
                                if (filename.endsWith('.json')) {
                                    const players = await parseMatchJSON(entry);
                                    for (const player of players) {
                                        if (profileRegex.test(player.playerId)) {
                                            const profile = player.playerId + ' ' + player.nickname;
                                            console.log(profile);
                                            profileDict[profile] = profileDict[profile] ? profileDict[profile] + 1 : 1;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }


            if (Object.keys(profileDict).length != 0) {
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
                    console.log(profileName);
                    playerTxt += profileName.toUpperCase() + "<br>";
                }
                console.log(profileArray);
                document.getElementById('players').innerHTML = playerTxt;
                txt = "";
            } else {
                txt = "OOOF! IT LOOKS LIKE THAT WASN'T A PROPER FILE<br>PLEASE SELECT (A) NEW FILE(S) TO TRY AGAIN";
                document.getElementById('fileLabel').innerHTML = "GIVE IT ANOTHER SHOT";
            }
        }
    } else {
        if (x.value == "") {
            txt += "SELECT ONE OR MORE FILES.";
        } else {
            txt += "THE FILES PROPERTY IS NOT SUPPORTED BY YOUR BROWSER!";
            txt += "<br>THE PATH OF THE SELECTED FILE: " + x.value; // If the browser does not support the files property, it will return the path of the selected file instead. 
        }
    }
    document.getElementById("status").innerHTML = txt;
}


// async function parseFile(file, nFiles, stop) {
//     if ('name' in file) {
//         if (file.name.endsWith('.zip')) {
//             const entries = await unzipArchive(file);
//             if (entries.length) {
//                 // get first entry content as text by using a TextWriter
//             }
//         } else if (file.name.endsWith('.json')) {

//         }
//     }
// }


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
    const text = await file.getData(
        // writer
        new zip.TextWriter(),
        // options
        {
            onprogress: (index, max) => {
                // onprogress callback
            }
        }
    );
    const parsedJSON = JSON.parse(text);
    if ('playerMatchStats' in parsedJSON) {
        return parsedJSON.playerMatchStats;
    }
    return [];
}