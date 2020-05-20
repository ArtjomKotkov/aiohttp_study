import {arts} from './arts_component.js'

$(document).ready(function () {
    var app = new Vue({
        el: '#app',
        data: {
        },
        delimiters: ['[[', ']]'],
        components: {
            'arts':arts
        }
    })
});