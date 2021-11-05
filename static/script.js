async function convertTimestamps() {
    const timestamps = document.querySelectorAll('.ts,.ts-team');

    for (let i = 0; i < timestamps.length; i++) {
        let tsDiv = timestamps[i].innerHTML;

        try {
            const tsDate = new Date(tsDiv);

            tsDiv = tsDate.getFullYear() + '-' + (tsDate.getMonth() + 1).toString().padStart(2, '0') + '-' + tsDate.getDate().toString().padStart(2, '0') + ' ' + tsDate.toLocaleTimeString('en-US');

            timestamps[i].innerHTML = tsDiv;

        } catch (e) {
            console.log(e);
        }
    }
}