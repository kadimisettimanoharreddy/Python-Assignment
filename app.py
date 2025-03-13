from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
import os

# Load AWS credentials from environment variables
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION")

# Validate required environment variables
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION]):
    raise ValueError("Missing required AWS environment variables")

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Initialize S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

@app.route('/')
def index():
    """ List all S3 buckets """
    try:
        buckets = s3_client.list_buckets().get('Buckets', [])
    except Exception as e:
        flash(f"Error fetching buckets: {str(e)}", 'danger')
        buckets = []
    return render_template('index.html', buckets=buckets)

@app.route('/bucket/<bucket_name>')
def list_files(bucket_name):
    """ List all files in the given bucket """
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name).get('Contents', [])
        if objects is None:
            objects = []
    except Exception as e:
        flash(f"Error fetching files: {str(e)}", 'danger')
        objects = []
    return render_template('bucket.html', bucket_name=bucket_name, objects=objects)

@app.route('/create_bucket', methods=['POST'])
def create_bucket():
    """ Create a new S3 bucket """
    bucket_name = request.form['bucket_name']
    try:
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': AWS_REGION})
        flash('Bucket created successfully!', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('index'))

@app.route('/delete_bucket/<bucket_name>', methods=['POST'])
def delete_bucket(bucket_name):
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name).get('Contents', [])
        if objects:
            for obj in objects:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

        versions = s3_client.list_object_versions(Bucket=bucket_name).get('Versions', [])
        delete_markers = s3_client.list_object_versions(Bucket=bucket_name).get('DeleteMarkers', [])

        for version in versions:
            s3_client.delete_object(Bucket=bucket_name, Key=version['Key'], VersionId=version['VersionId'])
        
        for marker in delete_markers:
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])

        s3_client.delete_bucket(Bucket=bucket_name)
        flash('Bucket deleted successfully!', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('index'))

@app.route('/upload_file/<bucket_name>', methods=['POST'])
def upload_file(bucket_name):
    file = request.files['file']
    if file:
        s3_client.upload_fileobj(file, bucket_name, file.filename)
        flash('File uploaded successfully!', 'success')
    return redirect(url_for('list_files', bucket_name=bucket_name))

@app.route('/delete_file/<bucket_name>/<file_key>')
def delete_file(bucket_name, file_key):
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        flash('File deleted successfully!', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('list_files', bucket_name=bucket_name))

@app.route('/move_file/<bucket_name>', methods=['POST'])
def move_file(bucket_name):
    destination_bucket = request.form.get('destination_bucket')
    file_key = request.form.get('file_key')
    destination_key = request.form.get('destination_key', file_key)
    
    if not all([destination_bucket, file_key]):
        flash('Missing parameters. Please provide destination bucket and file name.', 'danger')
        return redirect(url_for('list_files', bucket_name=bucket_name))
    
    try:
        s3_client.copy_object(
            Bucket=destination_bucket,
            CopySource={'Bucket': bucket_name, 'Key': file_key},
            Key=destination_key
        )
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        flash('File moved successfully!', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('list_files', bucket_name=bucket_name))

@app.route('/copy_file/<bucket_name>', methods=['POST'])
def copy_file(bucket_name):
    destination_bucket = request.form.get('destination_bucket')
    file_key = request.form.get('file_key')
    destination_key = request.form.get('destination_key', file_key)

    if not all([destination_bucket, file_key]):
        flash('Missing parameters. Please provide destination bucket and file name.', 'danger')
        return redirect(url_for('list_files', bucket_name=bucket_name))

    try:
        s3_client.copy_object(
            Bucket=destination_bucket,
            CopySource={'Bucket': bucket_name, 'Key': file_key},
            Key=destination_key
        )
        flash(f'File copied successfully to {destination_bucket}!', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('list_files', bucket_name=bucket_name))

if __name__ == '__main__':
    app.run(debug=True)

 
  















