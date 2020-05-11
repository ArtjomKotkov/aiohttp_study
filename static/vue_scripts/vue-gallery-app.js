
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

    Vue.component('control-album', {
        template: `
            <div class='d-flex flex-row'>
                <button @click='selectable()'>Выбор</button>
                <button @click='new_'>Добавить</button>
                <div v-if='create_new'>
                    
                </div>
            </div>
        `,
        data: function () {
            return {
                albums: null,
                create_new: false,
            }
        },
        methods: {
            selectable() {
                this.$emit('turnSelect');
            },
            new_ () {
                console.log('asfsf')
            }
        }
    });

    Vue.component('albums', {
        template: `
        <div class='d-flex flex-row justify-content-start align-items-center'>
            <div class='albums-header d-flex flex-row justify-content-start align-items-center'>
                <control-album @turnSelect='selectable = true'></control-album>
            </div>
            <div class='albums-body'>
                <div v-for='album in albums'>
                    <input type="checkbox" @click='selected.push(album.id)'>
                    <div class='album_name'>{{album.name}} </div>
                    <div class='album_body'></div>
                </div>
            </div>
        </div>`,
        data: function () {
            return {
                albums: null,
                selectable: false,
                selected: []
            }
        },
        methods: {
            test () {
                console.log('asfsaf')
            }
        },
        mounted() {
            axios.get(`/content/album?arts=6&user=${this.$root.user}&fields=id,name,description`, {
            }).then((response) => {
                this.albums = response.data.items
              console.log(response.data.items)
            }).catch((error) => {
              console.error(error);
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