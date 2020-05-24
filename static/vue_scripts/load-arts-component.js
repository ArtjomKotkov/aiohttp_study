import {search} from './search_component.js'

export {load_arts};

var load_arts = Vue.component('load-arts', {
	props:['owner', 'album_prop'],
    template: `
    <div class='d-fles flex-column align-items-center'>
        <div class='drag-and-drop-load_arts shadow p-0 w-75 h-75' v-if='pre_loaded'>
            <div v-if='full_loaded == false'>
                <img src="/static/img/loading.gif" alt="" />
            </div>
            <div v-if='full_loaded == true' class='h-100 p-3'>
                <img class='close d-inline-block' @click='close_and_clear' src="https://img.icons8.com/material-sharp/24/000000/railroad-crossing-sign--v2.png"/>
                <div class='h-100 d-flex flex-row justify-content-start align-items-center'>
                    <div ref='drop_zone' class='w-50 h-100 drag-and-drop-zone' @dragover.prevent @drop.prevent='ondrop' @dragenter.prevent='ondragenter' @dragleave.prevent='ondragleave' style='background-color:#bdbdbd;'>
                        <img :src="file.img" alt="" :style='loaded_img_zone_img'/>
                    </div>
                    <div class='w-50 h-100 p-3'>
                        <p class='mb-0'>Введите название изображения</p>
                        <hr class='drag-and-drop-items-hr'>
                        <input :style='style' v-model='file.name' type="text" class='d-block new-art-input'/>
                        <p class='mb-0'>Введите описание (необязательное поле)</p>
                        <hr class='drag-and-drop-items-hr'>
                        <textarea v-model='file.description' style='resize=none;' class='d-block new-art-input'></textarea>
                        <template v-if='album_prop == null'>
                            <p class='mb-0'>Выберите альбом (необязательное поле)</p>
                            <hr class='drag-and-drop-items-hr'>
                            <select v-model='file.album' class='d-block new-art-input'>
                              <option v-for='album in aviable_albums' :value='album.id'>{{album.name}}</option>
                            </select>
                        </template>
                        <p class='mb-0'>Выберите теги (необязательное поле)</p>
                        <hr class='drag-and-drop-items-hr'>
                        <search_tags @pushTags='file.tags=$event'>
							<template v-slot:description>
	                            Начните вводить тег, или введите '*'
	                        </template>
                        </search_tags>
                        <a href="#" class='mt-3 mx-auto d-block default-button button_focus text-center' @click.prevent='axios_load_art'>Загрузить</a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Еще ничего не загружено -->

        <div class='drag-and-drop-load_arts shadow d-flex flex-row justify-content-center align-items-center w-50 h-50' v-if='!pre_loaded'>
            <img class='close d-inline-block' @click='close_and_clear' src="https://img.icons8.com/material-sharp/24/000000/railroad-crossing-sign--v2.png"/>
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
            scale: null,
            valid: null,
            invalid_style: {
            	'-webkit-box-shadow': '0px 0px 14px 0px rgba(255,0,0,0.69)',
				'-moz-box-shadow': '0px 0px 14px 0px rgba(255,0,0,0.69)',
				'box-shadow': '0px 0px 14px 0px rgba(255,0,0,0.69)',
				'border':'1px solid red'
            },
            aviable_albums: null,
        }
    },
    computed: {
    	style () {
    		return (this.valid == false) ? this.invalid_style : '' 
    	},
        dnd_img () {
            if (this.selected != null && this.files.length != 0) {
                return this.files[this.selected].img
            } else {
                return '/static/img/loading.gif'
            }
        },
        loaded_img_zone_img () {
        	return this.scale[0] > this.scale[1] ? {display: 'block',height: '100%',margin: 'auto',} : {display: 'block',width: '100%',margin: 'auto'}
        },
    },
    watch: {

    },
    methods: {
    	axios_load_art () {
    		if (this.file.name == '' || this.file.name == null) {
    			return this.valid = false;
    		}
    		var form_data = new FormData();

    		form_data.append('name', this.file.name);
            if (this.album_prop == null) {
    		  form_data.append('album', this.file.album);
            } else {
                form_data.append('album', parseInt(this.album_prop))
            }
    		form_data.append('description', this.file.description);
    		var tags = [];
    		if (this.file.tags.length > 0) {
	    		tags = this.file.tags[0].name;
	    		for (var i = 1; i < this.file.tags.length; i++) {
	    			tags = tags + ',' + this.file.tags[i];
	    		}
    		}
    		form_data.append('tags', tags);
    		form_data.append('file', this.file.file);
    		axios({
    		  method: 'post',
    		  url: '/content/art',
    		  data: form_data,
    		  headers: {
		        'Content-Type': 'multipart/form-data'
    		  }
    		}).then((response) => {
    		  document.location.reload(true);
    		}).catch((error) => {
    		  console.error(error);
    		}).finally(() => {
    		  console.log('test')
    		});
  
    	},
        close_and_clear () {
            this.file = {}
            this.pre_loaded = false
            this.full_loaded = false
            this.errors = {}
            this.$emit('close_arts')
        },
        ondrop(e) {
            let dt = e.dataTransfer;
            let files = dt.files;
            for (var i = 0; i < files.length; i++) {
                this.file = {
                    file:files[i],
                    name:null,
                    description:null,
                    album:null,
                    tags:[],
                    img: '/static/img/loading.gif',
                    valid: false,
                }
                this.pre_loaded = true;
                var reader = new FileReader();
                reader.onload = () => {
                    this.file.img = reader.result;
                    var image = new Image();
                    image.src = reader.result;
                    image.onload = () => {
                        this.scale = this.check_scale(image.width, image.height);
                    };
                };
                reader.readAsDataURL(files[i])
            }
        },
        check_scale (width, height) {
            var scale = height / width;
            if(scale > 2 || scale < 0.6) {
                return this.errors['scale_error'] = 'Недопустимный масштаб изображения'
            }
            this.full_loaded = true;
            if (this.album_prop == null) {
                axios.get(`/content/album?user=${this.owner}&fields=id,name`, {
                }).then((response) => {
                  this.aviable_albums = response.data.items
                });
            }
            return [height, width]
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