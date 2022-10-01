
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
vizElement.style.width = getWidth() == 0 ? '400px' : '100%';
vizElement.style.minHeight = '700px';
vizElement.style.maxHeight = '900px';


// ADD PARAM TO FORCE EITHER DESKTOP OR MOBILE LAYOUT
var deviceElementvizElement = document.getElementById('deviceParam')
deviceElementvizElement.value = isMobile ? "mobile" : "desktop";

// ADD TABLEAU JS
var scriptElement = document.createElement('script');
scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
vizElement.parentNode.insertBefore(scriptElement, vizElement);
