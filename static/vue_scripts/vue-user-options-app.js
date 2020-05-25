
$(document).ready(function () {

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
								Новый пароль
							</div>
							<div class='user_option_change_item_text'>
								Повторите пароль
							</div>
						</div>
						<div class='d-flex flex-column justify-content-start align-items-left'>
							<input type="password" class='m-1' v-model='password_field.data1' :class='{ "field-valid" : password_field.valid1, "field-invalid" : invalid(password_field.valid1)}'/>
							<input type="password" class='m-1' v-model='password_field.data2' :class='{ "field-valid" : password_field.valid2, "field-invalid" : invalid(password_field.valid2)}'/>
						</div>
						<div>
							<a href="#" @click.prevent class='user_option_change_item_text'>Применить</a>
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
							<div class='user_option_change_item_text'>
								Повторите email
							</div>
						</div>
						<div class='d-flex flex-column justify-content-start align-items-left'>
							<input type="text" class='m-1' v-model='email_field.data1' :class='{ "field-valid" : email_field.valid1, "field-invalid" : invalid(email_field.valid1)}'/>
							<input type="text" class='m-1' v-model='email_field.data2' :class='{ "field-valid" : email_field.valid2, "field-invalid" : invalid(email_field.valid2)}'/>
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
	        	selected: null,
	        	password_field: {
	        		data1: null,
	        		data2: null,
	        		errors: {},
	        		valid1: null,
	        		valid2: null
	        	},
	        	email_field: {
	        		data1: null,
	        		data2: null,
	        		errors: {},
	        		valid1: null,
	        		valid2: null
	        	},
	        }
	    },
	    watch: {
	    	password_field: {
	    		deep: true,
	    		handler () {
	    			if( !field_is_empty(this.password_field.data1) && this.password_field.data1.length < 8) {
	    				this.password_field.errors['length'] = 'Длина пароля должна быть не менее 8 символов'
	    				this.password_field.valid1 = false
	    			} else {
	    				delete this.password_field.errors.length
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
	    				this.password_field.errors['equal'] = 'Пароли должны совпадать'
	    				this.password_field.valid2 = false
	    			} else {
	    				if (field_is_empty(this.password_field.data1) && !field_is_empty(this.password_field.data2)) {
	    					this.password_field.valid2 = false
	    				} else if (field_is_empty(this.password_field.data2) && field_is_empty(this.password_field.data1)) {
	    					this.password_field.valid2 = null
	    				} else {
	    					this.password_field.valid2 = true
	    				}
	    			}

	    		}
	    	},
	    	email_field: {
	    		deep: true,
	    		handler (new_) {
	    			if (this.email_field.data1 != '' && this.email_field.data2 != '' && this.email_field.data2 != this.email_field.data1) {
	    				this.email_field.errors['equal'] = 'Email\'ы должны совпадать'
	    				this.email_field.valid2 = false
	    			} else {
	    				if (this.email_field.data2 == '' && this.email_field.data1 == '') {
	    					this.email_field.valid2 = null
	    				} else {
	    					this.email_field.valid2 = true
	    				}
	    			}
	    			const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/i;
	    			if(!field_is_empty(this.email_field.data1)){

	    				this.email_field.valid1 = re.test(this.email_field.data1.toLowerCase())
	    			}
	    			this.check_email_debounce(new_.data1);
	    		}
	    	}
	    },
	    created: function () {
		    this.check_email_debounce = _.debounce(this.check_email, 1000)
		},
		methods: {
			check_email () {
				// Проверка на то занят ли
			},
			invalid (field_validation) {
				return field_validation == false ? true : false
			}
		},
	    computed: {
	    	email_text () {
	    		return this.user.email === undefined ? '~None~' : this.user.email
	    	}
	    }
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
		    		<img :src="user_img" alt="" id='user_options_left_menu_img'/>
		    	</div>
		    	<div class='user_options_left_menu_description'>
		    		<p text-align='center'>{{description}}</p>
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
                return this.user.photo != null ? this.user.photo : '/static/img/no-user-photo.png'
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