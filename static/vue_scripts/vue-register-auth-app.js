$(document).ready(function () {

	var global_styles = {
    	invalid: {
    		border:'1px solid red',
    	},
    	valid: {
    		border:'1px solid green',
    	}
    }

	custom_form = Vue.component('register-form', {
		props: ['url'],
		template: `
			<form :action="url" class='d-flex flex-column form-register' method='POST'>
				<input v-model='name_field.data' :style='style(name_field.valid)' name="name" type="text" placeholder='Nickname input'/>
				<ul v-if='Object.keys(name_field.errors).length != 0'>
					<li>{{name_field.errors.user_exist}}</li>
				</ul>
				<input v-model='password_field.data' :style='style(password_field.valid)' name='password' type="text" placeholder='Password'/>
				<ul v-if='Object.keys(password_field.errors).length != 0'>
					<li>{{password_field.errors._lenght}}</li>
				</ul>
				<input v-model='password2_field.data' name='password2' :style='style(password2_field.valid)' type="text" placeholder='Confirm password'/>
				<ul v-if='Object.keys(password2_field.errors).length != 0'>
					<li>{{password2_field.errors.equal}}</li>
				</ul>
				<input :disabled='!form_valid' type="submit" />
			</form>
		`,
		data: function () {
            return {
                name_field: {
                	data:null,
                	valid: null,
                	errors: {}
                },
                password_field: {
                	data:null,
                	valid: null,
                	errors: {},
                	min_lenght: 8
                },
                password2_field: {
                	data:null,
                	valid: null,
                	errors: {}
                },
                styles: global_styles
            }
        },
        watch: {
        	name_field: {
        			handler: function (new_, old) {
        				this.check_name_delay(new_.data);
        			},
        			deep: true
        		},
        	password_field: {
        			handler: function (new_, old) {
        				if (new_.data == '') {
        					this.password_field.valid = true;
		        			delete this.password_field.errors._lenght
		        		} else {
		        			if (new_.data.length < this.password_field.min_lenght) {
		        				this.password_field.valid = false;
		        				this.password_field.errors['_lenght'] = 'Минимальная длина пароля 8 символов.'
		        			} else {
		        				this.password_field.valid = true;
		        				delete this.password_field.errors._lenght
		        			}
		        		}
		        		this.check_password2(this.password2_field.data);
        			},
        			deep: true
        		},
        	password2_field: {
        			handler: function (new_, old) {
	        			this.check_password2(new_.data);
        			},
        			deep: true
        		},
        },
        created: function () {
		    this.check_name_delay = _.debounce(this.check_name, 1000)
		},
		computed: {
			form_valid: function() {
				if((this.name_field.valid == true && this.password_field.valid == true && this.password2_field.valid == true) && this.name_field.data != '' && this.password_field.data != '' && this.password2_field.data != '') {
					return true
				} else {
					return false
				}
			}
		},
		methods: {
			check_name(name) {
				if (name == '') {
					delete this.name_field.errors.user_exist
					return;
				}
				axios({
	                method: 'get',
	                url: `/user/manage/${name}?exist=True`,
					contentType: 'application/json'
	            })
	            .then((response) => {
	                if (response.data.exist == true) {
	                	this.name_field.valid = false;
	                	this.name_field.errors['user_exist'] = 'Такой пользователь уже существует.'
	                } else {
	                	this.name_field.valid = true;
	                	delete this.name_field.errors.user_exist
	                }  
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
			check_password2 (new_) {
				if (new_ != this.password_field.data) {
    				this.password2_field.valid = false;
    				this.password2_field.errors['equal'] = 'Пароли должны совпадать.'
    			} else {
    				this.password2_field.valid = true;
    				delete this.password2_field.errors.equal
    			}
			}
		}
	})

	auth_form = Vue.component('auth-form', {
		props: ['url'],
		template: `
			<form :action="url" class='d-flex flex-column form-register' method='POST'>
				<input v-model='name_field.data' :style='style(name_field.valid)' name="name" type="text" placeholder='Nickname input'/>
				<ul v-if='Object.keys(name_field.errors).length != 0'>
					<li>{{name_field.errors.user_exist}}</li>
				</ul>
				<input v-model='password_field.data' :style='style(password_field.valid)' name='password' type="text" placeholder='Password'/>
				<ul v-if='Object.keys(password_field.errors).length != 0'>
					<li>{{password_field.errors.correct_password}}</li>
				</ul>
				<input type="submit" @click.prevent='submit()' />
			</form>
		`,
		data: function () {
            return {
                name_field: {
                	data:null,
                	valid: null,
                	errors: {}
                },
                password_field: {
                	data:null,
                	valid: null,
                	errors: {},
                	min_lenght: 8
                },
                styles: global_styles
        	}
        },
        watch: {
        	
        },
		methods: {
			submit () {
				data = {
					name: this.name_field.data,
					password: this.password_field.data
				}
				var form = new FormData()
				form.append('name', this.name_field.data);
				form.append('password', this.password_field.data);
				axios({
	                method: 'POST',
	                url: this.url,
					data: form
	            })
	            .then((response) => {
	            	console.log(response)
	                if (response.status == 200) {
	                	document.location.href = `/`;
	                } 
	            })
	            .catch((error) => {
	            	if (error.response.status == 401) {
	                	this.password_field.valid = false;
	                	this.password_field.errors['correct_password'] = 'Неправильный пароль'	
	                } else if (error.response.status == 404) {
	                	this.name_field.valid = false;
	                	this.name_field.errors['user_exist'] = 'Такой пользователь не существует'
	                }
	            });
	 

			},
			check_name(name) {
				if (name == '') {
					delete this.name_field.errors.user_exist
					return;
				}
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