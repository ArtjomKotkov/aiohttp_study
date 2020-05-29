

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

	Vue.component('safety-options', {
		props: ['user'],
	    template: `
	    	<div class='p-3'>
	    		<div>
					<div class='d-flex flex-row justify-content-between align-items-center'>
						<div class='w-25 text-left'>Пароль</div>
						<div class='w-50 text-center'>************</div>
						<a href="#" class='d-block w-25 text-right' v-if='selected != 1' @click.prevent='selected = 1'>Изменить</a>
						<a href="#" class='d-block w-25 text-right' v-if='selected == 1' @click.prevent='selected = null'>Отмена</a>
					</div>
					<div v-if='selected == 1' class='d-flex flex-row justify-content-between align-items-top user_option_change_item'>
						<div>
							<div class='user_option_change_item_text'>
								Текущий пароль
							</div>
							<div class='user_option_change_item_text'>
								Новый пароль
							</div>
							<div class='user_option_change_item_text'>
								Повторите пароль
							</div>
						</div>
						<div class='d-flex flex-column justify-content-start align-items-left'>
							<input type="password" class='m-1 field-default' v-model='password_field.check'/>
							<input type="password" class='m-1 field-default' v-model='password_field.data1' :class='{ "field-valid" : password_field.valid1, "field-invalid" : invalid(password_field.valid1)}'/>
							<input type="password" class='m-1 field-default' v-model='password_field.data2' :class='{ "field-valid" : password_field.valid2, "field-invalid" : invalid(password_field.valid2)}'/>
							<errors-block :errors='password_field.errors'></errors-block>
						</div>
						<div>
							<a href="#" @click.prevent='change_password' class='user_option_change_item_text'>Применить</a>
						</div>
					</div>
	    		</div>
	    		<hr>
	    		<div>
					<div class='d-flex flex-row justify-content-between align-items-center'>
						<div class='w-25 text-left'>EMail</div>
						<div class='w-50 text-center'>{{email_text}}</div>
						<a href="#" class='d-block w-25 text-right' v-if='selected != 2' @click.prevent='selected = 2'>Изменить</a>
						<a href="#" class='d-block w-25 text-right' v-if='selected == 2' @click.prevent='selected = null'>Отмена</a>
					</div>
					<div v-if='selected == 2' class='d-flex flex-row justify-content-between align-items-top user_option_change_item'>
						<div>
							<div class='user_option_change_item_text'>
								Новый email
							</div>
						</div>
						<div class='d-flex flex-column justify-content-start align-items-left'>
							<input type="text" class='m-1 field-default' v-model='email_field.data' :class='{ "field-valid" : email_field.valid, "field-invalid" : invalid(email_field.valid)}'/>
							<errors-block :errors='email_errors'></errors-block>
						</div>
						<div>
							<a href="#" @click.prevent='change_email' class='user_option_change_item_text'>Применить</a>
						</div>
					</div>
	    		</div>
	    		<hr>
	    	</div>
	    `,
	    data: function () {
	        return {
	        	selected: null,
	        	password_field: {
	        		data1: null,
	        		data2: null,
	        		errors: {},
	        		valid1: null,
	        		valid2: null,
	        		check: null
	        	},
	        	email_field: {
	        		data: null,
	        		errors: {},
	        		valid: null,
	        	},
	        	email_errors: {}
	        }
	    },
	    watch: {
	    	password_field: {
	    		deep: true,
	    		handler () {
	    			if( !field_is_empty(this.password_field.data1) && this.password_field.data1.length < 8) {
	    				this.$set(this.password_field.errors, 'length', 'Длина пароля должна быть не менее 8 символов.');
	    				this.password_field.valid1 = false
	    			} else {
	    				this.$delete(this.password_field.errors, 'length');
	    				if (field_is_empty(this.password_field.data2) && field_is_empty(this.password_field.data1)) {
	    					this.password_field.valid1 = null
	    				} else {
	    					if (!field_is_empty(this.password_field.data1)){
	    						this.password_field.valid1 = true
	    					} else {
	    						this.password_field.valid1 = null
	    					}
	    				}
	    			}
	    			if (!field_is_empty(this.password_field.data1) && this.password_field.data2 != this.password_field.data1) {
	    				this.$set(this.password_field.errors, 'equal', 'Пароли должны совпадать.');
	    				this.password_field.valid2 = false
	    			} else {
	    				if (field_is_empty(this.password_field.data1) && !field_is_empty(this.password_field.data2)) {
	    					this.password_field.valid2 = false
	    				} else if (field_is_empty(this.password_field.data2) && field_is_empty(this.password_field.data1)) {
	    					this.password_field.valid2 = null
	    				} else {
	    					this.$delete(this.password_field.errors, 'equal');
	    					this.password_field.valid2 = true
	    				}
	    			}

	    		}
	    	},
	    	email_field: {
	    		deep: true,
	    		handler (new_) {
	    			this.check_email_debounce(new_.data1);
	    		}
	    	}
	    },
	    created: function () {
		    this.check_email_debounce = _.debounce(this.check_email, 1000)
		},
		methods: {
			change_email () {
				var form = new FormData();
				form.append('email', this.email_field.data)
				axios({
				  method: `POST`,
				  url: `/user/user_api/${this.user.name}`,
				  data: form
				}).then((response) => {
				  
				}).catch((error) => {
				  console.error(error.response.message);
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
			invalid (field_validation) {
				return field_validation == false ? true : false
			},
		},
	    computed: {
	    	email_text () {
	    		return this.user.email === undefined ? '~None~' : this.user.email
	    	}
	    },
	})

	Vue.component('common-options', {
		props: ['user'],
	    template: `
	    	<div class='p-3'>
	    		<div>
					<div class='d-flex flex-row justify-content-between align-items-center'>
						<div class='w-25 text-left'>Имя пользователя</div>
						<div class='w-50 text-center'>{{user.name}}</div>
						<a href="#" class='d-block w-25 text-right' v-if='selected != 1' @click.prevent='selected = 1'>Изменить</a>
						<a href="#" class='d-block w-25 text-right' v-if='selected == 1' @click.prevent='selected = null'>Отмена</a>
					</div>
					<div v-if='selected == 1' class='d-flex flex-row justify-content-between align-items-top user_option_change_item'>
						<div>
							Новое имя пользователя
						</div>
						<div>
							<input type="text" />
							
						</div>
						<div>
							<a href="#" @click.prevent class='user_option_change_item_text'>Применить</a>
						</div>
					</div>
	    		</div>
	    		<hr>
	    		<div>
					<div class='d-flex flex-row justify-content-between align-items-center'>
						<div class='w-25 text-left'>Аватар</div>
						<div class='w-50 text-center'>{{photo_text}}</div>
						<a href="#" class='d-block w-25 text-right' v-if='selected != 2' @click.prevent='selected = 2'>Изменить</a>
						<a href="#" class='d-block w-25 text-right' v-if='selected == 2' @click.prevent='selected = null'>Отмена</a>
					</div>
					<div v-if='selected == 2' class='d-flex flex-row justify-content-between align-items-top user_option_change_item'>
						<div>
							<div class='user_option_change_item_text'>
								Новый аватар
							</div>
						</div>
						<div class='d-flex flex-column justify-content-start align-items-left'>
							<input type="file" class='m-1' />
						</div>
						<div>
							<a href="#" @click.prevent class='user_option_change_item_text'>Применить</a>
						</div>
					</div>
	    		</div>
	    		<hr>
	    	</div>
	    `,
	    data: function () {
	        return {
	        	selected: null
	        }
	    },
	    computed: {
	    	photo_text () {
	    		return this.user.photo === undefined ? '~None~' : '~Загружено~'
	    	}
	    }
	})

	var user_options = Vue.component('user-options', {
		props: ['user'],
	    template: `
	    <div id='user_options' class='d-flex flex-row shadow'>
		    <div class='h-100' id='user_options_left_menu'>
		    	<div class=''>
		    		<img :src="user_img" alt="" id='user_options_left_menu_img' class='rounded-circle'/>
		    	</div>
		    	<div class='user_options_left_menu_description px-2 pb-3 text-center'>
		    		{{description}}
		    	</div>
		    	<div class='d-flex flex-column justify-content-start align-items-left'>
					<div v-bind:class="{ option_menu_item_selected: selected == 1 }" class='change_cursor_pointer option_menu_item' @click.prevent='selected = 1'>Общее</div>
					<div v-bind:class="{ option_menu_item_selected: selected == 2 }" class='change_cursor_pointer option_menu_item' @click.prevent='selected = 2'>Безопасность</div>
		    	</div>
		    </div>
			<div class='h-100 w-100'>
				<common-options :user='user' v-if='selected == 1'></common-options>
				<safety-options :user='user' v-if='selected == 2'></safety-options>
		    </div>
	    </div>
	    `,
	    data: function () {
	        return {
	        	selected: 1,
	        }
	    },
	    computed: {
	    	description () {
	    		return this.user.description === undefined ? 'Без описания' : this.user.description
	    	},
            user_img () {
                return this.user.photo != null ? '/media/'+this.user.photo : '/static/img/no-user-photo.png'
            },
	    }
	})

	var app = new Vue({
	    el: '#app',
	    data: {
	    },
	    delimiters: ['[[', ']]'],
	})

})

function field_is_empty (data) {
	return data == '' || data == null ? true : false
}