resource "aws_s3_bucket" "public_put" {
  bucket_prefix = "codex-put-object-"
}

data "aws_iam_policy_document" "public_put" {
  statement {
    effect = "Allow"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.public_put.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "public_put" {
  bucket = aws_s3_bucket.public_put.id
  policy = data.aws_iam_policy_document.public_put.json
}

