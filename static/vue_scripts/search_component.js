		
export {search};

var search = Vue.component('search-input', {
	props: ['searchIcon', 'maxSelect'],
	inheritAttrs: false,
    template: `
    <div>
    	<div class='d-flex flex-row justify-content-start align-items-center input_search_box_input_outer'>
    		<div class='input_search_box_item d-block flex-shrink-0' v-for="(tag, index) in selected_tags"><span>{{tag.name}}</span><img @click='delete_tag' class='mx-1' style='margin: 6px 0; filter: opacity(20%);' src="/static/img/cross.png" width='12px' height='12px' alt="" /></div>
    		<input v-model='data' ref='input_to_focus' class=' p-2 input_search_box_input_inner flex-grow-1 flex-shrink-2 d-block' type="text" @focus="focused = true" @blur="focused = false">
    		<img class='mx-2 change_cursor_pointer' v-if="(selected_tags.length != 0 || data != '') && searchIcon == true" @click='search' src="/static/img/search.png" width='26px' height='26px' alt="" />
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
			if (this.selected_tags.length == this.maxSelect) {
				return;
			}
			if (this.selected_tags.includes(this.tags_match[index]) == false) {
				this.selected_tags.push(this.tags_match[index]);
				this.data = '';
				this.$refs.input_to_focus.focus();
			}
			this.$emit('pushTags', this.selected_tags);
		},
		delete_tag (index) {
			this.selected_tags.splice(index, 1);
		}            
    }  
})