import boto3, botocore

s3= boto3.client("s3")

def upload_file_to_s3(file, filename, bucket_name):
    try:
        s3.upload_fileobj(file, bucket_name, filename)
    except Exception as e:
        return str(e)
    return "Upload Successful"

def delete_object_from_s3(filename,bucket_name):
    try:
        bucket = bucket_name
        image_path = filename
        s3.delete_object(Bucket=bucket,Key=image_path)
    except Exception as e:
        return e
    return "Delete Successful"