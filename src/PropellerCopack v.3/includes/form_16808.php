<?php
	if (empty($_POST['name_5714_9473_27751_16808']) && strlen($_POST['name_5714_9473_27751_16808']) == 0 || empty($_POST['email_5714_9473_27751_16808']) && strlen($_POST['email_5714_9473_27751_16808']) == 0 || empty($_POST['message_5714_9473_27751_16808']) && strlen($_POST['message_5714_9473_27751_16808']) == 0)
	{
		return false;
	}
	
	$name_5714_9473_27751_16808 = $_POST['name_5714_9473_27751_16808'];
	$email_5714_9473_27751_16808 = $_POST['email_5714_9473_27751_16808'];
	$message_5714_9473_27751_16808 = $_POST['message_5714_9473_27751_16808'];
	$optin_5714_9473_27751_16808 = $_POST['optin_5714_9473_27751_16808'];
	
	// Create Message	
	$to = 'mbrown@propellerinc.com';
	$email_subject = "New quote request from Propeller website";
	$email_body = "You have received a new contact form submission from the Propeller website. \n\nName_5714_9473_27751_16808: $name_5714_9473_27751_16808 \nEmail_5714_9473_27751_16808: $email_5714_9473_27751_16808 \nMessage_5714_9473_27751_16808: $message_5714_9473_27751_16808 \nOptin_5714_9473_27751_16808: $optin_5714_9473_27751_16808 \n";
	$headers = "MIME-Version: 1.0\r\nContent-type: text/plain; charset=UTF-8\r\n";	
	$headers .= "From: noreply@propellerinc.com\r\n";
	$headers .= "Reply-To: $email_5714_9473_27751_16808";

	// Post Message
	if (function_exists('mail'))
	{
		$result = mail($to,$email_subject,$email_body,$headers);
	}
	else // Mail() Disabled
	{
		$error = array("message" => "The php mail() function is not available on this server.");
	    header('Content-Type: application/json');
	    http_response_code(500);
	    echo json_encode($error);
	}	
?>