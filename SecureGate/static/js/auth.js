
function setupFormValidation(formSelector, inputSelector, submitButtonSelector, onSubmit) {
    "use strict";

    // Validate form inputs
    function validateForm() {
        var input = $(formSelector).find(inputSelector);
        var check = true;

        input.each(function(index, element) {
            if (!validate(element)) {
                showValidate(element);
                check = false;
            }
        });

        if (check) {
            onSubmit(); // Call the provided callback function
        }
    }

    // Form submission handler
    function handleFormSubmission(event) {
        event.preventDefault(); // Prevent the default form submission
        validateForm();
    }

    // Hide validation messages on focus
    $(formSelector).find(inputSelector).each(function() {
        $(this).focus(function() {
            hideValidate(this);
        });
    });

    // Attach click event listener to the submit button
    $(submitButtonSelector).on('click', handleFormSubmission);

    // Validation function
    function validate(input) {
        if ($(input).attr('type') == 'email' || $(input).attr('name') == 'email') {
            if (!$(input).val().trim().match(/^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{1,5}|[0-9]{1,3})(\]?)$/)) {
                return false;
            }
        } else {
            if ($(input).val().trim() == '') {
                return false;
            }
        }
        return true;
    }

    // Show validation message
    function showValidate(input) {
        var thisAlert = $(input).parent();
        $(thisAlert).addClass('alert-validate');
    }

    // Hide validation message
    function hideValidate(input) {
        var thisAlert = $(input).parent();
        $(thisAlert).removeClass('alert-validate');
    }
}





$(document).ready(function() {
  if (document.getElementById('login')) {
      setupFormValidation('.validate-form', '.input100', '#login', function() {
        // Callback function to handle form submission
        submitLoginForm();
      });
  }
});


function recoverPassword(){
	$("form")[0].innerHTML= `
	${csrf_middleware_token.outerHTML}		
	<span class="myform100-form-title" style="
    padding-bottom: 20px;
">Forgot password</span><span class="myform100-form-title" style="
    font-size: 11px;
    color: #4343f1;
    text-align: center;
    padding-bottom: 30px;
">Enter your details then we will get back to you</span>

					<div class="wrap-input100 validate-input" data-validate="Valid username is required">
						<input class="input100" type="text" name="username" placeholder="Username">
						<span class="focus-input100"></span>
						<span class="symbol-input100">
							<i class="fa fa-user" aria-hidden="true"></i>
						</span>
					</div>

          <div class="wrap-input100 validate-input" data-validate="Valid email is required: ex@abc.xyz">
						<input class="input100" type="text" name="email" placeholder="Email">
						<span class="focus-input100"></span>
						<span class="symbol-input100">
							<i class="fa fa-envelope" aria-hidden="true"></i>
						</span>
					</div>

					
					
					<div class="container-myform100-form-btn">
						<button class="myform100-form-btn" id="password-reset">Send</button>
					</div>

					<div class="text-center p-t-136">
						<a onclick="goToLogin()" class="txt2" href="#login">
							Go back to login	
							<i class="fa fa-long-arrow-left m-l-5" aria-hidden="true"></i>
						</a>
					</div>
`;
    setupFormValidation('.validate-form', '.input100', '#password-reset', function() {
      // Callback function to handle form submission
      submitPassResetForm();
    });
}








function requestAccess(){
	$("form")[0].innerHTML=`
	${csrf_middleware_token.outerHTML}
<form class="myform100-form validate-form">
		<span class="myform100-form-title" style="
    font-size: 11px;
    color: #4343f1;
    text-align: center;
    padding-bottom: 10px;
">Enter your details then we will get back to you</span>

<select style="margin-bottom: 25px; height: 44px" class="input" name="ticket_type">
<option value="" selected="">Choose category</option>
<option value="incident">Report an issue</option>
<option value="request">Request access</option>
</select>


<textarea class="form-textarea" name="description"></textarea>

<div class="wrap-input100 validate-input" data-validate="Valid email is required: ex@abc.xyz" style="
margin-top: 30px;">
      <input class="input100" type="text" name="email" placeholder="Email">
      <span class="focus-input100"></span>
      <span class="symbol-input100">
        <i class="fa fa-envelope" aria-hidden="true"></i>
      </span>
</div>

<div class="container-myform100-form-btn">
<button type="submit" style="margin-top: 30px" class="myform100-form-btn">
  Send
</button>
</div>

<div class="text-center p-t-25">
<a href="#login" onclick="goToLogin()" class="txt2">
    Go back to login
  <i class="fa fa-long-arrow-left m-l-5" aria-hidden="true"></i>
</a>
</div>
				</form>
`;
$("form")[0].id = "create-ticket-form";
prepareTicketForm();
}







function goToLogin(){
	$("form")[0].innerHTML= `
	${csrf_middleware_token.outerHTML}
	<span class="hidden-login-title"> Login </span>

  <div class="wrap-input100 validate-input" data-validate="Valid username is required">
    <input class="input100" type="text" name="username" placeholder="Username">
    <span class="focus-input100"></span>
    <span class="symbol-input100">
      <i class="fa fa-user" aria-hidden="true"></i>
    </span>
  </div>

  <div class="wrap-input100 validate-input" data-validate="Password is required">
    <input class="input100" type="password" name="password" placeholder="Password">
    <span class="focus-input100"></span>
    <span class="symbol-input100">
      <i class="fa fa-lock" aria-hidden="true"></i>
    </span>
  </div>

  <span class="myform100-form-title" style="font-size: 12px; color: red; text-align: center; padding: 5px" id="login_error"></span>

  <div class="container-myform100-form-btn">
    <button type="submit" class="myform100-form-btn" id="login">Login</button>
  </div>

  <div class="text-center p-t-12">
    <span class="txt1"> Forgot </span>
    <a onclick="recoverPassword()" class="txt2" href="#forgotpassword">
      Password?
    </a>
  </div>

  <div class="text-center p-t-100">
    <a onclick="requestAccess()" class="txt2" href="#requestaccess">
        Request access/ report an issue
      <i class="fa fa-long-arrow-right m-l-5" aria-hidden="true"></i>
    </a>
  </div>
	`

  // front end bug fix for login view: padding change
  function applyClassReplacement() {
    var element = document.getElementsByClassName("hidden-login-title")[0];
    element.classList.replace("hidden-login-title", "myform100-form-title");
  }
  setTimeout(applyClassReplacement, 0);

    setupFormValidation('.validate-form', '.input100', '#login', function() {
      // Callback function to handle form submission
      submitLoginForm();
    });
    
  }

let csrf_middleware_token = document.getElementsByName("csrfmiddlewaretoken")[0];




function submitLoginForm() {
	var form = $("form")[0];
  var formData = new FormData(form);

    $.ajax({
		url: '../xloginapi/', 
		type: 'POST', 
		data: formData,
		processData: false,
		contentType: false,
		success: function(response) {
			console.log('Logged in successfully', response);
			window.open("../","_self");
		},
		error: function(xhr, status) {
			console.error('Could not login you in with provided credentials. Status:', status, 'Response:', xhr.responseText);
			document.getElementById("login_error").innerText = "Could not log you in with the provided credentials";
			
		}
	});
}

// pasword reset request ticket logged
function submitPassResetForm() {
	var form = $("form")[0];
  var formData = new FormData(form);

    $.ajax({
		url: '/password_reset_request/', 
		type: 'POST', 
		data: formData,
		processData: false,
		contentType: false,
		success: function(response) {
			
      if (response.error){
        document.getElementById("password-reset").parentElement.outerHTML = `
        <span class="myform100-form-title" 
        style="font-size: 12px; 
        color: red; 
        text-align: center; 
        padding: 5px"">${response.error}</span> ${document.getElementById("password-reset").parentElement.outerHTML}
        `;
      } else if (response.status===200){
        console.log(response.message);
        document.getElementsByTagName("form")[0].
        outerHTML = `<form class="myform100-form validate-form">
                        <span class="myform100-form-title" style="
                          padding-bottom: 20px; color:green
                      ">Request Successful!</span><span class="myform100-form-title" style="
                          font-size: 11px;
                          color: #4343f1;
                          text-align: center;
                          padding-bottom: 30px;
                      "> ${response.message} </span>
                      <span class="myform100-form-title" style="
                      font-size: 11px;
                      color: #4343f1;
                      text-align: center;
                      padding-bottom: 30px;
                    ">We will get back to you as soon as possible.</span>

                    <div class="text-center p-t-100">
                        <a onclick="goToLogin()" class="txt2" href="#login">
                          Go back to login	
                          <i class="fa fa-long-arrow-left m-l-5" aria-hidden="true"></i>
                          </a>
                          </div>
                  </form>`
                    }
		},
		error: function(xhr, status) {
			document.getElementById("password-reset").parentElement.outerHTML = `
        <span class="myform100-form-title" 
        style="font-size: 12px; 
        color: red; 
        text-align: center; 
        padding: 5px">Error ${status} : ${xhr.responseText}</span> ${document.getElementById("password-reset").parentElement.outerHTML}
        `;
		}
	});
}


async function clearAllCookies() {
  return new Promise((resolve, reject) => {
    var cookies = document.cookie.split(";");
    var cookiePromises = [];

    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i];
      var eqPos = cookie.indexOf("=");
      var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
      var cookiePromise = new Promise((resolve, reject) => {
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
        resolve();
      });
      cookiePromises.push(cookiePromise);
    }

    Promise.all(cookiePromises)
      .then(() => {
        resolve();
      })
      .catch((error) => {
        reject(error);
      });
  });
}


function submitLogout() {
  var form = $("form")[0];
  var formData = new FormData(form);

  $.ajax({
    url: '/xlogoutapi/',
    type: 'POST',
    data: formData,
		processData: false,
		contentType: false,
    success: function (response) {
      console.log('Logged out successfully');
      clearAllCookies();
      window.location.href = "/auth"; 
    },
    error: function (xhr, status) {
      console.error('Could not logout. Status:', status, 'Response:', xhr.responseText);
      clearAllCookies();
    }
  });
}



