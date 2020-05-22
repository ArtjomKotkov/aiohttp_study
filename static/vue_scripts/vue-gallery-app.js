import {arts} from './arts_component.js'
import {load_arts} from './load-arts-component.js'

$(document).ready(function () {

    var global_styles = {
        invalid: {
            border:'1px solid red',
        },
        valid: {
            border:'1px solid green',
        }
    }

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
                    <a href="#" :class='{button_focus: show == 2}' class='d-block default-button' @click.prevent='$emit("showChange", 2)'>Все изображения</a>
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
                <div v-show='show == 2' class='pt-3' v-if='$root.user == $root.owner'>
                    <div class='d-flex flex-row justify-content-center align-items-center'>
                        <a href='#' ref='new_album_button' @click.prevent='new_arts_load = true' class='default-button'>
                            Загрузить арт
                        </a>
                    </div>
                    <load-arts :owner='$root.owner' v-if='new_arts_load' @close_arts='new_arts_load = false'></load-arts>
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
                styles:global_styles,
                new_arts_load: false,
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
                    var data = {
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
        },
        components: {
            'load-arts':load_arts
        }
    });

    Vue.component('albums', {
        template: `
        <div class='d-flex flex-column justify-content-start align-items-center'>
            <div class='albums-header'>
                <control-album :show='show' :selected='selected' @turnSelect='turnSelecton' @deleteAlbums='delete_albums' @addAlbum='add_album' @showChange='change_show'></control-album>
            </div>
            <div class='albums-body w-100 d-flex flex-row justify-content-center align-items-top' v-if='show == 1'>
                <div v-for='album in albums' class='change_cursor_pointer single-album-block overflow-hidden' @mouseenter='show_name = album.id' @mouseleave='show_name = null' @click='enter_album(album.id)'>
                    <input type="checkbox" v-if='selectable' @change='select_album(album.id)' style='z-index:205;'>
                    <div class='album_name' v-if='show_name == album.id'>{{album.name}}</div>
                    <div class='album_body' style='position:relative;'>
                        <div>
                            <template v-for='(row, index1) in album.arts'>
                                <img v-for="(item, index2) in row" :style="offset(item.offsetX, item.offsetY)" v-bind:src="/media/ + item.path" class="art-album-preview">
                            </template>
                        </div>
                    </div>
                </div>
            </div>
            <arts v-if='show == 2' :get_request='"/content/art?user=" + $root.owner'></arts>
        </div>`,
        data: function () {
            return {
                albums: null,
                selectable: false,
                selected: [],
                show: 1,
                show_name: null,
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
                    var new_albums = []
                    for (var i = 0; i < this.albums.length; i++) {
                        if (!this.selected.includes(this.albums[i].id)) {
                            new_albums.push(this.albums[i]);
                        }
                    }
                    this.albums = new_albums;
                    this.selected = [];
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
            },
            offset (valueX, valueY) {
              return `transform: translateX(${ valueX }) translateY(${ valueY })`
            },
            enter_album (id) {
                document.location.href = `/user/${this.$root.owner}/gallery/${id}`;
            }
        },
        mounted() {
            axios.get(`/content/album?arts=9&user=${this.$root.owner}&fields=id,name,description`, {
            }).then((response) => {
                this.albums = response.data.items
                for(var i = 0; i < this.albums.length; i++) {
                    if (this.albums[i].arts.length > 0) {
                        this.albums[i].arts = create_array(this.albums[i].arts, 3, 100) 
                    }
                }
            });
        },
        components: {
            'arts':arts
        }
    })

	var app = new Vue({
        el: '#app',
        data: {
            owner: null,
            user: null,
        },
        delimiters: ['[[', ']]'],
    })

});


function create_array (info, arts_in_line, art_width) {
    var multi_array = [];
    // Create mulri array
    for (var index = 0; index < info.length; index = index + arts_in_line) {
        multi_array.push(info.slice(index, index+arts_in_line));
    }
    // Save vertical offsets
    var top_offset = [];
    var center_offset = 0;
    for (var row = 0; row < multi_array.length; row ++) {
        for (var col = 0; col < multi_array[row].length; col ++) {
            // scale of art
            let scale = art_width / multi_array[row][col]['width'];
            if (row == 0 && col == 0) {
                center_offset = 90 - multi_array[0][0]['height'] * scale
            } 
            // Calculation new height and offsetX/Y values
            if (row == 0) {
                top_offset[col] = parseInt(multi_array[row][col]['height'] * scale) + 1 + center_offset;
                multi_array[row][col]['offsetY'] = 0 + center_offset + 'px';
                multi_array[row][col]['offsetX'] = (art_width+1) * col -47.5 + 'px';
            } 
            else {
                multi_array[row][col]['offsetY'] = top_offset[col] + 'px';
                top_offset[col] = top_offset[col] + parseInt(multi_array[row][col]['height']) * scale + 1;
                multi_array[row][col]['offsetX'] = (art_width+1) * col -47.5 + 'px';
            }
        }
    }
    return multi_array;
}