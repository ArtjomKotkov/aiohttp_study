
$(document).ready(function () {

    Vue.directive('click-outside', {
      bind: function (el, binding, vnode) {
        this.event = function (event) {
          if (!(el == event.target || el.contains(event.target))) {
            vnode.context[binding.expression](event);
          }
        };
        document.body.addEventListener('click', this.event)
      },
      unbind: function (el) {
        document.body.removeEventListener('click', this.event)
      },
    });

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
        props: ['selected'],
        template: `
            <div class=''>
                <div class='d-flex flex-row justify-content-center align-items-center'>
                    <a href="#" :class='{button_focus: show == 1}' class='d-block default-button' autofocus @click.prevent='show = 1'>Альбомы</a>
                    <a href="#" :class='{button_focus: show == 2}'' class='d-block default-button' @click.prevent='show = 2'>Все изображения</a>
                </div>
                <div v-show='show == 1' class='pt-3'>
                    <div class='d-flex flex-row justify-content-center align-items-center'>
                        <a href='#' ref='new_album_button' @click.prevent='create_new = true' class='default-button'>
                            Новый альбом
                        </a>
                        <a href='#' class='default-button' @click='$emit("turnSelect")'>Выбор</a>
                        <a href='#' v-if='selected.length != 0' class='error-button' @click=''>Удалить выбранное</a>
                        <div ref='new_album_window' v-if='create_new' class='new-album-block d-inline-block shadow'>
                            <img class='close d-inline-block' @click='create_new = false' src="https://img.icons8.com/material-sharp/24/000000/railroad-crossing-sign--v2.png"/>
                            <div class='d-flex flex-column justify-content-around align-items-center h-100'>
                                <span class='new-album-header d-block header_menu_block_header'>Создание нового альбома</span>
                                <hr>
                                <input v-model='album_name' type="text">
                                <input type="submit" @click.prevent='create_new_album'>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `,
        data: function () {
            return {
                albums: null,
                create_new: false,
                show: 1,
                album_name: null,
            }
        },
        watch: {
            album_name: function(new_, old) {
                //check if album with name alreay exist, add check to view
            } 
        },
        methods: {
            selectable() {
                this.$emit('turnSelect');
            },
            close(event) {
                if (Object.is(event.target, this.$refs.new_album_window) == true) {
                    return;
                }
            },
            create_new_album () {
                console.log(this.$root.user )
                data = {
                                   name: this.album_name,
                                   owner: this.$root.user 
                                }
                axios.post('/content/album', {
                  data
                }).then((response) => {
                  // TODO
                }).catch((error) => {
                  console.error(error);
                });
            }
        }
    });

    Vue.component('albums', {
        template: `
        <div class='d-flex flex-column justify-content-start align-items-center'>
            <div class='albums-header'>
                <control-album :selected='selected' @turnSelect='turnSelecton'></control-album>
            </div>
            <div class='albums-body w-100 d-flex flex-row justify-content-start align-items-top'>
                <div v-for='album in albums' class='single-album-block'>
                    <input type="checkbox" v-if='selectable' @change='select_album(album.id)'>
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
            turnSelecton () {
                this.selected = [];
                if (this.selectable == true) {
                    this.selectable = false;
                } else {
                    this.selectable = true;
                }
            },
            select_album (id) {
                if (this.selected.includes(id) == true) {
                    this.selected.splice( this.selected.indexOf(id), 1 );
                } else {
                    this.selected.push(id)
                }
            }
        },
        mounted() {
            axios.get(`/content/album?arts=6&user=${this.$root.user}&fields=id,name,description`, {
            }).then((response) => {
                this.albums = response.data.items
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