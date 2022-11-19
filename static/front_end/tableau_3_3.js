
// CAPTURES CURRENT WIDTH OF SCREEN
// USED TO DECIDE DESKTOP/MOBILE
function getWidth() {
return Math.max(
    document.body.scrollWidth,
    document.documentElement.scrollWidth,
    document.body.offsetWidth,
    document.documentElement.offsetWidth,
    document.documentElement.clientWidth
);
}

// ADD WIDTH AND HEIGHT
var divElement = document.getElementById('viz1664118452778');
var vizElement = divElement.getElementsByTagName('object')[0];
var isMobile = getWidth() < 600
vizElement.style.width = '100%';
vizElement.style.minHeight = isMobile ? '650px' : '875px';
vizElement.style.maxHeight = '900px';

console.log(getWidth())

// ADD PARAM TO FORCE EITHER DESKTOP OR MOBILE LAYOUT
var deviceElementvizElement = document.getElementById('deviceParam')
deviceElementvizElement.value = isMobile ? "phone" : "desktop";

// PRE-FILTER TO USER'S DEFAULT SET
if (localStorage) {
    var storedSet = (localStorage.getItem("set") ?? "2000").toUpperCase();
    var deviceElementvizElement = document.getElementById('filterParam')
    deviceElementvizElement.value = `Set=${storedSet}`;
    console.log(`Populating Explore Set - ${storedSet}`)
}

// ADD TABLEAU JS
var scriptElement = document.createElement('script');
scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
vizElement.parentNode.insertBefore(scriptElement, vizElement);
