
$(document).ready(function () {


    Vue.component('user_init', {
        props: ['owner'],
        template: `<span v-if='false'>{{owner}}</span>`,
        data: function () {
            return {
            }
        },
        mounted() {
            this.$root.user = this.owner
        }
    })

    Vue.component('albums', {
        template: `
        <div class='d-flex flex-row justify-content-start align-items-center'>
            <div v-for='album in albums'>
                <div class='album_name'></div>
                <div class='album_body'></div>
            </div>
        </div>`,
        data: function () {
            return {
                albums: null,
            }
        },
        mounted() {
            axios.get('/content/albums', {
              params: {
              },
            }).then((response) => {
              // TODO
            }).catch((error) => {
              console.error(error);
            }).finally(() => {
              // TODO
            });
        }
    })

	var app = new Vue({
        el: '#app',
        data: {
            user: null,
        },
        mounted() {

        },
        methods: {

        },
        delimiters: ['[[', ']]'],
    })

});