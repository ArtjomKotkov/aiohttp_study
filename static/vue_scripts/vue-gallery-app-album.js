import {arts} from './arts_component.js'
import {load_arts} from './load-arts-component.js'


$(document).ready(function () {
    
    Vue.component('user_init', {
        props: ['owner', 'user', 'album'],
        template: `<span v-if='false'>{{owner}}</span>`,
        data: function () {
            return {
            }
        },
        mounted() {
            this.$root.owner = this.owner
            this.$root.user = this.user
            this.$root.album = this.album
        }
    })

    Vue.component('control-album', {
        props: ['selected', 'show'],
        template: `
            <div class=''>
                <div class='pt-3' v-if='$root.user == $root.owner'>
                    <div class='d-flex flex-row justify-content-center align-items-center'>
                        <a href='#' ref='new_album_button' @click.prevent='new_arts_load = true' class='default-button'>
                            Загрузить арт
                        </a>
                    </div>
                    <load-arts :album_prop='$root.album' :owner='$root.owner' v-if='new_arts_load' @close_arts='new_arts_load = false'></load-arts>
                </div>
            </div>
        `,
        data: function () {
            return {
                new_arts_load: false,
            }
        },
    });

    var app = new Vue({
        el: '#app',
        data: {
            owner: null,
            user: null,
            album: null
        },
        delimiters: ['[[', ']]'],
        components: {
            'arts':arts,
            'load-arts':load_arts
        }
    })

});