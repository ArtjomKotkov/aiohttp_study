
	export {errors_component};

$(document).ready(function () {

	var errors_component = Vue.component('errors-block', {
		props:['errors'],
		template: `
			<div v-if='Object.keys(errors).length != 0' class='form-errors d-flex flex-column align-items-left justify-content-between'>
				<div v-for='error in Object.values(errors)'>{{error}}</div>
			</div>
		`,
		data: function () {
            return {

            }
        }
	})

	custom_form = Vue.component('register-form', {
		template: `
			<form class='d-flex flex-column form-register align-items-center w-100' method='POST'>
				
				<img v-if='image_field.url != null' class='rounded-circle mb-3' :src="image_field.url" alt="" />
				
				<input class='field-default' v-model='name_field.data' :class='{ "field-valid" : name_field.valid, "field-invalid" : invalid(name_field.valid)}' name="name" type="text" placeholder='Имя пользователя'/>
				<errors-block :errors='name_field.errors'></errors-block>

				<input class='field-default' v-model='email_field.data' :class='{ "field-valid" : email_field.valid, "field-invalid" : invalid(email_field.valid)}' name="email" type="text" placeholder='Email'/>
				<errors-block :errors='email_errors'></errors-block>

				<input class='field-default' v-model='password_field.data' :class='{ "field-valid" : password_field.valid, "field-invalid" : invalid(password_field.valid)}' name='password' type="password" placeholder='Введите пароль'/>
				<errors-block :errors='password_field.errors'></errors-block>
				
				<input class='field-default' v-model='password2_field.data' name='password2' :class='{ "field-valid" : password2_field.valid, "field-invalid" : invalid(password2_field.valid)}' type="password" placeholder='Подтвердите пароль'/>
				<errors-block :errors='password2_field.errors'></errors-block>
				
				<label for="file-upload" class="custom-file-upload d-block text-center">
				    Загрузить аватар
				</label>
				<input id="file-upload" type="file" @change='photoValidation'/>
				<errors-block :errors='image_field.errors'></errors-block>
				
				<input :disabled='!form_valid' type="submit" @click.prevent='register' class='field-default-submit'/>
			</form>
		`,
		data: function () {
            return {
                name_field: {
                	data:null,
                	valid: null,
                	errors: {}
                },
                email_field: {
                	data:null,
                	valid: null,
                },
                email_errors: {},
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
                image_field: {
                	data:null,
                	errors: {},
                	url:null
                },
            }
        },
        watch: {
        	email_field: {
        			handler: function (new_, old) {
        				
		    			if(!field_is_empty(this.email_field.data)){
		    				this.check_email_debounce(new_.data);
		    			}
		    			if(field_is_empty(this.email_field.data)){
		    				return this.email_field.valid = null;
		    			}
        			},
        			deep: true
        		},
        	name_field: {
        			handler: function (new_, old) {
        				if (field_is_empty(new_.data)) {
        					this.$delete(this.name_field.errors, 'user_exist')
        					return this.name_field.valid = null;
        				}
        				this.check_name_delay(new_.data);
        			},
        			deep: true
        		},
        	password_field: {
        			handler: function (new_, old) {
        				if (field_is_empty(new_.data)) {
        					this.$delete(this.password_field.errors, '_lenght')
        					return this.password_field.valid = null;
        				}
	        			if (new_.data.length < this.password_field.min_lenght) {
	        				this.password_field.valid = false;
	        				this.$set(this.password_field.errors, '_lenght', 'Минимальная длина пароля 8 символов.');
	        			} else {
	        				this.password_field.valid = true;
	        				this.$delete(this.password_field.errors, '_lenght');
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
		    this.check_email_debounce = _.debounce(this.check_email, 1000)
		},
		computed: {
			form_valid: function() {
				if(this.name_field.valid == true &&
				   this.password_field.valid == true &&
				   this.password2_field.valid == true &&
				   this.email_field.valid == true) {
					return true
				} else {
					return false
				}
			}
		},
		methods: {
			register () {
				if (!this.form_valid) {
					return;
				}
				var form = new FormData();
				form.append('name', this.name_field.data);
				form.append('email', this.email_field.data);
				form.append('password', this.password_field.data);
				form.append('photo', this.image_field.data, this.image_field.data.name);

				axios({
				  method: 'post',
				  url: '/user/user_api/',
				  data: form
				}).then((response) => {
				  window.location = "/user/auth/";
				}).catch((error) => {
				  console.log(error.response.data)
				}).finally(() => {
				  // TODO
				});
			},
			check_email () {
				axios({
				  method: 'get',
				  url: `/user/user_api/${this.email_field.data}?email=true&fields=email`,
				}).then((response) => {
			 		this.email_field.valid = false;
			 		this.$set(this.email_errors, 'email_exist', 'Пользователь с таким EMail адрессом уже существует.')
				}).catch((error) => {
				  	const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/i;
					this.email_field.valid = re.test(this.email_field.data.toLowerCase());
					if(re.test(this.email_field.data.toLowerCase()) == false) {
						this.email_field.valid = false;
						this.$set(this.email_errors, 'invalid_format', 'Неверный формат EMail.')
					} else {
						this.$delete(this.email_errors, 'invalid_format')
						this.email_field.valid = true;
					}
			 		this.$delete(this.email_errors, 'email_exist')
				});
			},
			photoValidation (event) {
				var reader = new FileReader();
				reader.onload = () => {
					var image = new Image();
					image.src = reader.result;
                    image.onload = () => {
                    	this.image_field.data = null;
                    	this.image_field.url = null;
                        if(image.width != image.height) {
                        	return this.$set(this.image_field.errors, 'invalid_scale', 'Соотношение сторон загружаемого изображения должно быть 1:1.');
                        } else {
                        	this.$delete(this.image_field.errors, 'invalid_scale');
                        }
                        if(image.width > 512 || image.height > 512) {
                        	return this.$set(this.image_field.errors, 'invalid_dimensions', 'Максимальные размеры изображения 512х512.');
                        } else {
                        	this.$delete(this.image_field.errors, 'invalid_dimensions');
                        }
                        this.image_field.data = event.target.files[0];
                        this.image_field.url = reader.result;
                    };
				};
				reader.readAsDataURL(event.target.files[0])
			},
			check_name(name) {
				axios({
	                method: 'get',
	                url: `/user/manage/${name}?exist=True`,
					contentType: 'application/json'
	            })
	            .then((response) => {
	                if (response.data.exist == true) {
	                	this.name_field.valid = false;
	                	this.$set(this.name_field.errors, 'user_exist', 'Такой пользователь уже существует.');
	                } else {
	                	this.name_field.valid = true;
	                	this.$delete(this.name_field.errors, 'user_exist');
	                }  
	            });
			},
			check_password2 (new_) {
				if (!field_is_empty(new_) && new_ != this.password_field.data) {
    				this.password2_field.valid = false;
    				this.$set(this.password2_field.errors, 'equal', 'Пароли должны совпадать.');
    			} else if (field_is_empty(new_)) {
    				this.password2_field.valid = null;
    				this.$delete(this.password2_field.errors, 'equal');
    			} else {
    				this.password2_field.valid = true;
    				this.$delete(this.password2_field.errors, 'equal');
    			}
			},
			invalid (field_validation) {
				return field_validation == false ? true : false
			},
		}
	})

	auth_form = Vue.component('auth-form', {
		props: ['url'],
		template: `
			<form class='d-flex flex-column form-register align-items-center w-100' method='POST'>

				<input class='field-default' v-model='name_field.data' :class='{ "field-valid" : name_field.valid, "field-invalid" : invalid(name_field.valid)}' name="name" type="text" placeholder='Nickname input'/>
				<errors-block :errors='name_field.errors'></errors-block>

				<input class='field-default' v-model='password_field.data' :class='{ "field-valid" : password_field.valid, "field-invalid" : invalid(password_field.valid)}' name='password' type="password" placeholder='Password'/>
				<errors-block :errors='password_field.errors'></errors-block>

				<input class='field-default-submit' type="submit" @click.prevent='submit()' />
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
        	}
        },
		methods: {
			submit () {
				if (field_is_empty(this.name_field.data) || field_is_empty(this.password_field.data)) {
					if(field_is_empty(this.name_field.data)) {
						this.$set(this.name_field.errors, 'blank_error', 'Поле должно быть заполнено.');
						this.name_field.valid = false;
					}
					if(field_is_empty(this.password_field.data)) {
						this.$set(this.password_field.errors, 'blank_error', 'Поле должно быть заполнено.');
						this.password_field.valid = false;
					}	
					return;
				}
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
	                if (response.status == 200) {
	                	document.location.href = `/`;
	                } 
	            })
	            .catch((error) => {
	            	if (error.response.status == 401) {
	                	this.password_field.valid = false;
	                	this.$set(this.password_field.errors, 'correct_password', 'Неправильный пароль')
	                } else if (error.response.status == 404) {
	                	this.name_field.valid = false;
	                	this.$set(this.name_field.errors, 'user_exist', 'Такой пользователь не существует')
	                }
	            });
			},
			invalid (field_validation) {
				return field_validation == false ? true : false
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

function field_is_empty (data) {
	return data == '' || data == null ? true : false
}