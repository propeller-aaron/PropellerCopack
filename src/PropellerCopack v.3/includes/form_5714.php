<?php
	if (empty($_POST['name_5714']) && strlen($_POST['name_5714']) == 0 || empty($_POST['email_5714']) && strlen($_POST['email_5714']) == 0 || empty($_POST['message_5714']) && strlen($_POST['message_5714']) == 0)
	{
		return false;
	}
	
	$name_5714 = $_POST['name_5714'];
	$email_5714 = $_POST['email_5714'];
	$message_5714 = $_POST['message_5714'];
	$optin_5714 = $_POST['optin_5714'];
	
	// Create Message	
	$to = 'mbrown@propellerinc.com';
	$email_subject = "New quote request from Propeller website";
	$email_body = "You have received a new contact form submission from the Propeller website. \n\nName_5714: $name_5714 \nEmail_5714: $email_5714 \nMessage_5714: $message_5714 \nOptin_5714: $optin_5714 \n";
	$headers = "MIME-Version: 1.0\r\nContent-type: text/plain; charset=UTF-8\r\n";	
	$headers .= "From: noreply@propellerinc.com\r\n";
	$headers .= "Reply-To: $email_5714";

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