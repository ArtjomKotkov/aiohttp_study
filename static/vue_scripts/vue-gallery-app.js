import {arts} from './arts_component.js'
import {search} from './search_component.js'

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

    Vue.component('load-arts', {
        template: `
        <div class='d-fles flex-column align-items-center'>
            <div class='drag-and-drop-load_arts shadow p-0' v-if='pre_loaded'>
                <div v-if='full_loaded == false'>
                    <img src="/static/img/loading.gif" alt="" />
                </div>
                <div v-if='full_loaded == true' class='h-100'>
                    <div v-if='format == 1' class='d-flex flex-row justify-content-start align-items-center h-100'>
                        <div class='h-100 loaded-img-zone-vertical'>
                            <img :src="file.img" alt="" class='loaded-img-zone-vertical-img'/>
                        </div>
                        <div>
                            <input type="text" />
                            <input type="text" />
                            <input type="text" />
                        </div>
                    </div>
                    <div v-if='format == 2' class='d-flex flex-column justify-content-start align-items-center h-100'>
                        <div class='w-100 loaded-img-zone-horizontal-img-outer' style='overflow:hidden; height=60%;'>
                            <img :src="file.img" alt="" class='loaded-img-zone-horizontal-img' width='100%'/>
                        </div>
                        <div>
                            <input type="text" />
                            <input type="text" />
                            <input type="text" />
                        </div> 
                    </div>
                </div>
            </div>

            <!-- Еще ничего не загружено -->

            <div class='drag-and-drop-load_arts shadow d-flex flex-row justify-content-center align-items-center' v-if='!pre_loaded'>
                <img class='close d-inline-block' @click='' src="https://img.icons8.com/material-sharp/24/000000/railroad-crossing-sign--v2.png"/>
                <div class='w-100 h-100'>
                    <div class='p-3 drag-and-drop-zone w-100 h-100' @dragover.prevent @drop.prevent='ondrop' @dragenter.prevent='ondragenter' @dragleave.prevent='ondragleave'>
                    </div>
                </div>
            </div>
        </div>`,
        data: function () {
            return {
                file:{},
                pre_loaded:false,
                full_loaded:false,
                errors: {
                },
                format: null
            }
        },
        computed: {
            dnd_img () {
                if (this.selected != null && this.files.length != 0) {
                    return this.files[this.selected].img
                } else {
                    return '/static/img/loading.gif'
                }
            },
        },
        watch: {

        },
        methods: {
            name_calc(name) {
                if (name == null) {
                    return 'Без имени'
                } else {
                    return name
                }
            },
            desc_calc(description) {
                if (description == null) {
                    return 'Пусто'
                } else {
                    return description
                }
            },
            ondrop(e) {
                let dt = e.dataTransfer;
                let files = dt.files;
                for (var i = 0; i < files.length; i++) {
                    this.file = {
                        file:files[i],
                        name:null,
                        description:null,
                        tags:[],
                        img: '/static/img/loading.gif',
                        valid: false,
                        tags: []
                    }
                    this.pre_loaded = true;
                    var reader = new FileReader();
                    reader.onload = () => {

                        this.file.img = reader.result;
                        var image = new Image();
                        image.src = reader.result;
                        image.onload = () => {
                            this.check_scale(image.width, image.height);
                        };

                    };
                    reader.readAsDataURL(files[i])
                }
            },
            check_scale (width, height) {
                var scale = height / width;
                console.log(scale)
                if(scale > 2 || scale < 0.6) {
                    return this.errors['scale_error'] = 'Недопустимный масштаб изображения'
                } else if (scale > 1) {
                    this.format = 1; // vertical
                    this.full_loaded = true;
                } else {
                    this.format = 2; // horizontal 
                    this.full_loaded = true;
                }
            },
            ondragenter() {
                console.log("test2")
            },
            ondragleave() {
                console.log("test3")
            },
            img_preview(file, i) {
                var reader = new FileReader();
                reader.onload = (event) => {
                    this.files[i].img = reader.result;
                };
                reader.readAsDataURL(file)
            }
        },
        components: {
            'search_tags':search
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
                <div v-show='show == 2' class='pt-3' v-if='$root.user == $root.owner'>
                    <div class='d-flex flex-row justify-content-center align-items-center'>
                        <a href='#' ref='new_album_button' @click.prevent='new_arts_load = true' class='default-button'>
                            Загрузить арт
                        </a>
                    </div>
                    <load-arts v-if='new_arts_load'></load-arts>
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
                new_arts_load: false
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
            <arts v-if='show == 2' :get_request='"/content/art?user=" + $root.owner'></arts>
        </div>`,
        data: function () {
            return {
                albums: null,
                selectable: false,
                selected: [],
                show: 1,
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
        mounted() {

        },
        methods: {

        },
        delimiters: ['[[', ']]'],
    })

});
