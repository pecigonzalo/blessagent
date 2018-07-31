#!/usr/bin/env python
import json
import os
import stat

import boto3
import click


@click.command()
@click.option('--region', envvar='AWS_REGION', help='AWS Region where BLESS runs')
@click.option('--function-name', default='BLESS', help='Name of the BLESS lambda function')
@click.option('--hostname', multiple=True, help='Hostname to allow on this certificate', required=True)
@click.option('--key-in', type=click.File('rb'), required=True)
@click.option('--key-cert-out', type=click.Path(), required=True)
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(region, function_name, hostname, key_in, key_cert_out, verbose):

    public_key = key_in.read().strip().decode()

    payload = {
        'hostnames': ",".join(hostname),
        'public_key_to_sign': public_key
    }
    payload_json = json.dumps(payload)

    click.secho('Invoking {} in {}'.format(function_name, region), fg='green')
    if verbose:
        click.echo('payload_json is: \'{}\''.format(
            payload_json))

    lambda_client = boto3.client('lambda', region_name=region)
    response = lambda_client.invoke(FunctionName=function_name,
                                    InvocationType='RequestResponse', LogType='None',
                                    Payload=payload_json)
    if verbose:
        click.echo('{}\n'.format(response['ResponseMetadata']))

    if response['StatusCode'] != 200:
        click.secho('Error creating cert.', fg='red')
        return -1

    payload = json.loads(response['Payload'].read())

    if 'certificate' not in payload:
        click.secho(str(payload), fg='red')
        return -1

    cert = payload['certificate']

    with os.fdopen(os.open(key_cert_out, os.O_WRONLY | os.O_CREAT, 0o600),
                   'w') as cert_file:
        cert_file.write(cert)
    # If cert_file already existed with the incorrect permissions, fix them.
    file_status = os.stat(key_cert_out)
    if 0o600 != (file_status.st_mode & 0o777):
        os.chmod(key_cert_out, stat.S_IRUSR | stat.S_IWUSR)

    click.secho('Wrote Certificate to: ' + key_cert_out, fg='green')


if __name__ == '__main__':
    main()
