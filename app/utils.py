from app import s3, s3_bucket_name


def upload_to_s3(content, file_name):
    """Upload content to an S3 bucket."""
    try:
        s3.put_object(Bucket=s3_bucket_name, Key=file_name, Body=content)
        print(f"File '{file_name}' uploaded to S3 bucket '{s3_bucket_name}'.")
        return True
    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")
        return False
