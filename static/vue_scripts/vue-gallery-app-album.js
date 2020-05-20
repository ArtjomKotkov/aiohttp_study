import {arts} from './arts_component.js'

$(document).ready(function () {
    
    Vue.component('user_init', {
        props: ['owner', 'user'],
        template: `<span v-if='false'>{{owner}}</span>`,
        data: function () {
            return {
            }
        },
        mounted() {
            this.$root.owner = this.owner
            this.$root.user = this.user
        }
    })

    var app = new Vue({
        el: '#app',
        data: {
            owner: null,
            user: null
        },
        delimiters: ['[[', ']]'],
        components: {
            'arts':arts
        }
    })

});