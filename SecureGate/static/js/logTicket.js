function prepareTicketForm(){
    document.getElementsByName("description")[0].value = 'Name: \nContact Number: \nQuery information: \n';
    $('#create-ticket-form').on('submit', function(event) {
        event.preventDefault(); // Prevent default form submission

        // Serialize form data
        var formData = $(this).serialize();

        // Send AJAX request
        $.ajax({
            url: '/create_ticket/', 
            type: 'POST',
            data: formData,
            dataType: 'json', // Expect JSON response
            success: function(response) {
                // Handle success response
                let goto = document.getElementsByClassName('txt2')[0].outerHTML;
                document.getElementsByTagName("form")[0]
                .outerHTML = `<form class="myform100-form validate-form">
                                <span class="myform100-form-title" style="
                                padding-bottom: 20px; color:green
                            ">Query Logged Successfully!</span><span class="myform100-form-title" style="
                                font-size: 11px;
                                color: #4343f1;
                                text-align: center;
                                padding-bottom: 30px;
                            "> Your query reference: ${response.reference} </span>
                            <span class="myform100-form-title" style="
                            font-size: 11px;
                            color: #4343f1;
                            text-align: center;
                            padding-bottom: 80px;
                            ">We will get back to you as soon as possible.</span>

                            ${goto}
                        </form>`;
                
                // fix style (center txt2 goto text)
                document.getElementsByClassName('txt2')[0].style.marginLeft = '90px';
            },
            error: function(xhr, status, error) {
                // Handle error response
                console.error('Error: ' + error);

            }
        });
    });
}


