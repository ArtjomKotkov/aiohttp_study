$(document).ready(function () {

	custom_form = Vue.component('custom-form', {
		template: `
			<form action="#">
				<input v-model='name' :style='style()' name="name" type="text" placeholder='Nickname input'/>
				<p>{{name_errors}}</p>
				<input name='password' type="text" placeholder='Password'/>
				<input name='password2' type="text" placeholder='Confirm password'/>
			</form>
		`,
		data: function () {
            return {
                name: null,
                password: null,
                password2: null,
                //
                name_errors: null,
                password_errors: null,
                password2_errors: null,
                //
                name_valid: null,
                password_valid: null,
                password2_valid: null,
                invalid_style: {
                	border:'1px solid red',
                },
                valid_style: {
                	border:'1px solid green',
                },
                default_style: {
                },
            }
        },
        watch: {
        	name: function (new_, old) {
        		this.check_name_delay(new_);
        	}
        },
        created: function () {
		    this.check_name_delay = _.debounce(this.check_name, 1000)
		},
		methods: {
			check_name(name) {
				if (name == '') {
					return;
				}
				axios({
                method: 'get',
                url: `/user/manage/${name}?exist=True`,
				contentType: 'application/json'
	            })
	            .then((response) => {
	                if (response.data.exist == true) {
	                	this.name_valid = false;
	                } else {
	                	this.name_valid = true;
	                }
	                console.log(this.name_valid)
	            });
			},
			style () {
				if (this.name_valid == false) {
					return this.invalid_style;
				}
				if (this.name_valid == true) {
					return this.valid_style;
				}					
				return this.default_style;
			}
		}
	})

	var app = new Vue({
        el: '#app',
        data: {

        },
        delimiters: ['[[', ']]'],
        computed: {
            
        },

    })

})