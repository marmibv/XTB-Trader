$(document).ready(function () {
    // Dynamically load the jQuery library if it hasn't been loaded already
    if (typeof jQuery === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://code.jquery.com/jquery-3.6.3.min.js';
        document.getElementsByTagName('head')[0].appendChild(script);
    }

    // Use a setTimeout to wait for the buttons to be rendered before hiding them
    setTimeout(function () {
        $("#hide-button").click(function () {
            if($("#info").is(":visible")) 
                $("#info").hide();
            else {
                $("#info").show();
            }
        });
    }, 2000); // Adjust the delay (in milliseconds) if needed
});