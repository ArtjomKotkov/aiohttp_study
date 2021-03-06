
$(document).ready(function () {

	search_input = Vue.component('search-input', {
		inheritAttrs: false,
        template: `
        <div>
        	<div class='d-flex flex-row justify-content-start align-items-center input_search_box_input_outer'>
        		<div class='input_search_box_item d-inline-block' v-for="(tag, index) in selected_tags"><span>{{tag.name}}</span><img @click='delete_tag' class='mx-1' style='margin: 6px 0; filter: opacity(20%);' src="/static/img/cross.png" width='12px' height='12px' alt="" /></div>
        		<input v-model='data' ref='input_to_focus' class=' p-2 input_search_box_input_inner flex-grow-1 d-inline-block' type="text" @focus="focused = true" @blur="focused = false">
        		<img class='mx-2 change_cursor_pointer' v-if="selected_tags.length != 0 || data != ''" @click='search' src="/static/img/search.png" width='26px' height='26px' alt="" />
        	</div>
        	<div v-if='focused && tags_match == null' class="shadow input_search_box_additional_box" id='input_search_box'>
        		<p><slot name='description'></slot></p>
        	</div>
        	<div v-if='tags_match != null' class="shadow input_search_box_additional_box" id='input_search_box'>
        		<div v-for='(tag, index) in tags_match' class="input_search_box_item d-inline-block" @click='select(index)'><span>{{tag.name}}</span></div>
        	</div>
        </div>`,
        data: function () {
            return {
                data: '',
                tags: null,
                tags_match: null,
                selected_tags: [],
                focused: false
            }
        },
        mounted() {
            axios({
                method: 'get',
                url: '/content/tag?limit=10000',
				contentType: 'application/json'
            })
            .then( (response) => {
                this.tags = response.data.items
            });
        },
        watch: {
        	data: function (oldData, newData) {
        		this.delay_search_like_tag();
        	}
        },
        created: function () {
		    this.delay_search_like_tag = _.debounce(this.search_like_tag, 500)
		},
        methods: {
        	search () {
        	},
			search_like_tag () {
				if (this.data == '*') {
					this.tags_match = this.tags
					return;
				}
				if (this.data == '') {
					return this.tags_match = null;
				}
				var buff_line = [];
				for (var i = 0, l = this.tags.length; i < l; i++) 
				{
				    if (this.tags[i].name.toLowerCase().includes(this.data.toLowerCase()) == true) {
				    	buff_line.push(this.tags[i])
				    }
				}
				if (buff_line.length != 0) {
					this.tags_match = buff_line;
				}
			},
			select (index) {
				if (this.selected_tags.includes(this.tags_match[index]) == false) {
					this.selected_tags.push(this.tags_match[index]);
					this.data = '';
					this.$refs.input_to_focus.focus();
				}
			},
			delete_tag (index) {
				this.selected_tags.splice(index, 1);
			}            
        }  
    })

	var app = new Vue({
        el: '#header',
        data: {
        },
        mounted() {
    //         this.window_width = window.innerWidth
    //         this.window_height = window.innerHeight 
    //         axios({
    //             method: 'get',
    //             url: '/content/art',
				// contentType: 'application/json'
    //         })
    //         .then(function (response) {
    //             app.raw = response.data.items.slice();
    //             var newObject = Object.assign({}, response.data.items)
    //             app.info = create_array(app.raw, app.arts_in_line, app.art_width)
    //         });
    //         window.addEventListener('resize', () => {
    //             if (app.raw !== null){
    //                 this.window_width = window.innerWidth
    //                 this.window_height = window.innerHeight 
    //                 app.info = create_array(this.raw, this.arts_in_line, this.art_width)
    //             }
    //         });
        },
        delimiters: ['[[', ']]'],
    	components: {
    		'search-input':search_input
    	}
    })

});