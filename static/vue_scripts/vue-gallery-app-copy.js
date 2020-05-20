
$(document).ready(function () {

    var global_styles = {
        invalid: {
            border:'1px solid red',
        },
        valid: {
            border:'1px solid green',
        }
    }

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

    Vue.component('control-album', {
        props: ['selected', 'show'],
        template: `
            <div class=''>
                <div class='d-flex flex-row justify-content-center align-items-center'>
                    <a href="#" :class='{button_focus: show == 1}' class='d-block default-button' autofocus @click.prevent='$emit("showChange", 1)'>Альбомы</a>
                    <a href="#" :class='{button_focus: show == 2}'' class='d-block default-button' @click.prevent='$emit("showChange", 2)'>Все изображения</a>
                </div>
                <div v-show='show == 1' class='pt-3' v-if='$root.user == $root.owner'>
                    <div class='d-flex flex-row justify-content-center align-items-center'>
                        <a href='#' ref='new_album_button' @click.prevent='create_new = true' class='default-button'>
                            Новый альбом
                        </a>
                        <a href='#' class='default-button' @click='$emit("turnSelect")'>Выбор</a>
                        <a href='#' v-if='selected.length != 0' class='error-button' @click='delete_albums'>Удалить выбранное</a>
                        <div ref='new_album_window' v-if='create_new' class='new-album-block d-inline-block shadow'>
                            <img class='close d-inline-block' @click='create_new = false' src="https://img.icons8.com/material-sharp/24/000000/railroad-crossing-sign--v2.png"/>
                            <div class='d-flex flex-column justify-content-around align-items-center h-100'>
                                <span class='new-album-header d-block header_menu_block_header'>Создание нового альбома</span>
                                <hr>
                                <input :style='style(album_field.valid)' v-model='album_field.data' type="text">
                                <ul v-if='Object.keys(album_field.errors).length != 0'>
                                    <li v-if='album_field.errors.unfilled'>{{album_field.errors.unfilled}}</li>
                                    <li v-if='album_field.errors.exist'>{{album_field.errors.exist}}</li>
                                </ul>
                                <input :disabled='valid()' type="submit" @click.prevent='create_new_album'>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `,
        data: function () {
            return {
                create_new: false,
                album_field: {
                    data:null,
                    valid: null,
                    errors: {}
                },
                styles:global_styles
            }
        },
        watch: {
            album_field: {
                handler: function (new_, old) {
                    if (new_.data == '') {
                        this.album_field.valid = false;
                        this.album_field.errors['unfilled'] = 'Поле не может быть пустым'
                        return;
                    }
                    for (var i = 0; i < this.$parent.albums.length; i++) {
                        if(this.album_field.data == this.$parent.albums[i].name) {
                            this.album_field.valid = false;
                            this.album_field.errors['exist'] = 'Альбом с таким именем уже существует'
                            return;
                        }
                    }
                    this.album_field.valid = true;
                    delete this.album_field.errors.exist
                    delete this.album_field.errors.unfilled
                },
                deep: true
            },
        },
        methods: {
            delete_albums () {
                if (this.selected.length == 0) {
                    return;
                } else {
                   this.$emit('deleteAlbums');
                }
            },
            selectable() {
                this.$emit('turnSelect');
            },
            close(event) {
                if (Object.is(event.target, this.$refs.new_album_window) == true) {
                    return;
                }
            },
            create_new_album () {
                    data = {
                       name: this.album_field.data,
                       owner: this.$root.owner 
                    }
                    axios.post('/content/album', {
                      data
                    }).then((response) => {
                        this.create_new = false;
                        this.album_field.data = null;
                        this.$emit('addAlbum', response.data.items[0])
                    }).catch((error) => {
                });
            },
            style (valid) {
                if (valid == false) {
                    return this.styles.invalid;
                }
                if (valid == true) {
                    return this.styles.valid;
                }                   
                return this.styles.default;
            },
            valid () {
                if (this.album_field.data == null) {
                    return true;
                }
                return (!(this.album_field.valid))
            }
        }
    });

    Vue.component('albums', {
        template: `
        <div class='d-flex flex-column justify-content-start align-items-center'>
            <div class='albums-header'>
                <control-album :show='show' :selected='selected' @turnSelect='turnSelecton' @deleteAlbums='delete_albums' @addAlbum='add_album' @showChange='change_show'></control-album>
            </div>
            <div class='albums-body w-100 d-flex flex-row justify-content-start align-items-top' v-if='show == 1'>
                <div v-for='album in albums' class='single-album-block'>
                    <input type="checkbox" v-if='selectable' @change='select_album(album.id)'>
                    <div class='album_name'>{{album.name}} </div>
                    <div class='album_body'></div>
                </div>
            </div>
            <div class="center" :style="{ width : center_div_width+'px', height : window_height+'px'}" v-if='show == 2'>
                <template v-for='(row, index1) in info'>
                    <photo v-for="(item, index2) in row" :item="item" :art_width='art_width' :menu='$refs.menu'></photo>
                </template>
            </div>
        </div>`,
        data: function () {
            return {
                albums: null,
                selectable: false,
                selected: [],
                show: 1,
                raw: null,
                info: null,
                art_width: 250,
                window_width: null,
                window_height: null,
            }
        },
        methods: {
            change_show (show_num) {
                this.show = show_num;
            },
            delete_albums() {
                axios.delete('/content/album', {
                    data:JSON.stringify({ids:this.selected})
                }).then((response) => {
                    new_albums = []
                    console.log(this.selected)
                    for (var i = 0; i < this.albums.length; i++) {
                        if (!this.selected.includes(this.albums[i].id)) {
                            new_albums.push(this.albums[i]);
                        }
                    }
                    this.albums = new_albums;
                    this.selected = [];
                }).catch((error) => {
                  console.error(error);
                }).finally(() => {
                  // TODO
                });
            },
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
            },
            add_album (item) {
                this.albums.push(item);
            }
        },
        mounted() {
            axios.get(`/content/album?arts=6&user=${this.$root.owner}&fields=id,name,description`, {
            }).then((response) => {
                this.albums = response.data.items
            }).catch((error) => {
              console.error(error);
            });
            this.window_width = window.innerWidth
            this.window_height = window.innerHeight 
            axios({
                method: 'get',
                url: '/content/art',
                contentType: 'application/json'
            })
            .then((response) => {
                this.raw = response.data.items.slice();
                var newObject = Object.assign({}, response.data.items)
                this.info = create_array(this.raw, app.arts_in_line, this.art_width)
            });
            window.addEventListener('resize', () => {
                if (app.raw !== null){
                    this.window_width = window.innerWidth
                    this.window_height = window.innerHeight 
                    app.info = create_array(this.raw, this.arts_in_line, this.art_width)
                }
                
            });
        },
        computed: {
            arts_in_line () {0
                var value = parseInt((this.window_width - 24*2) / (this.art_width+10));
                if (value < 1) {
                    value = 1;
                }
                return value;
            },
            center_div_width ()  {
                return this.arts_in_line * (this.art_width + 10)
            }
        },
    })

    Vue.component('photo', {
        props: ['item', 'art_width', 'menu'],
        template: `<span class='art' :style="offset(item.offsetX, item.offsetY)" @mouseover="hover = true" @mouseout="hover = false">
                        <img v-bind:src="/media/ + item.path" class="img" :width="art_width+'px'" @click='enter_art'>
                        <a href="#" class='art-owner' align="center" v-show='hover'>{{item.owner}}</a>
                        <a href="#" class='art-menu' align="center" v-show='hover' ref='menu_button' @click.prevent='menu.open($event, $refs.menu_button, item)'>...</a>
                   </span>`,
        data: function () {
            return {
                hover: false,
            }
        },
        methods: {
            offset (valueX, valueY) {
              return `transform: translateX(${ valueX }) translateY(${ valueY })`
            },
            enter_art () {
                document.location.href = `/user/${this.item.owner}/art/${this.item.id}`;
            }
        },
    })

	var app = new Vue({
        el: '#app',
        data: {
            owner: null,
            user: null,
        },
        mounted() {

        },
        methods: {

        },
        delimiters: ['[[', ']]'],
    })

});

function create_array(info, arts_in_line, art_width) {
    var multi_array = [];
    // Create mulri array
    for (var index = 0; index < info.length; index = index + arts_in_line) {
        multi_array.push(info.slice(index, index+arts_in_line));
    }
    // Save vertical offsets
    var top_offset = []
    for (var row = 0; row < multi_array.length; row ++) {
        for (var col = 0; col < multi_array[row].length; col ++) {
            // scale of art
            let scale = art_width / multi_array[row][col]['width'];
            // Calculation new height and offsetX/Y values
            if (row == 0) {
                top_offset[col] = parseInt(multi_array[row][col]['height'] * scale) + 10;
                multi_array[row][col]['offsetY'] = 0;
                multi_array[row][col]['offsetX'] = (art_width+10) * col + 'px';
            } 
            else {
                multi_array[row][col]['offsetY'] = top_offset[col] + 'px';
                top_offset[col] = top_offset[col] + parseInt(multi_array[row][col]['height']) * scale + 10;
                multi_array[row][col]['offsetX'] = (art_width+10) * col + 'px';
            }
        }
    }
    return multi_array;
}