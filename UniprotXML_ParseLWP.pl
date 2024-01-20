use strict;
use warnings;

use LWP::Simple;
use XML::Simple qw(:strict);
use Data::Dumper;


my $browser = LWP::UserAgent->new;

my $filename = "./Resources/UniProt2_1.txt";

open(my $fh, '<encoding(UTF-8)', $filename) or die "Could not open '$filename' $!";


my @ids = ();

#checks if the protein ids are correct, and eliminates excess whitespace
while (my $rows = <$fh>){
  $rows =~ s/^\s+|\s+$//g;  
  if ($rows =~ /:\s*([A-Za-z][0-9]{5})/){
	push(@ids, $1)
}
  else{
	print "error:". $rows. "\n";
}
}

my %final_Hash;
foreach (@ids){
	#URL differs based on each element in the @ids
	my $url = "https://www.uniprot.org/uniprot/$_.xml";
	
	#set every element in our @ids array to a variable prot_id, make this an undefined key in our final Hash.
	#The final Hash will be a key (prot_id) and a hash reference as value pair. The hash reference will include a hash with
	#name, fullname, and sequence keys.
	my $prot_id = $_;  
	$final_Hash{$prot_id} = undef;
	
	my $response = $browser->get($url, 'User-Agent' => 'Mozilla/4.0 (compatible; MSIE 7.0)');
	if ($response->is_success) {
		# We got something.
		print 'Content type is ', $response->content_type, "\n";
		if ($response->content_type eq "application/xml") {
			#entry_Hash will be created once a valid xml has been found, this is the Hash reference linked to a key in final_Hash
			my %entry_Hash;
			print "Process an XML response\n";
			my $xml = new XML::Simple();
			my $data = $xml->XMLin($response->content, forcearray=>[qw(dbReference)], keyattr=>[]);
			#print Dumper($data);

			# This gives the level under the entry node
			my $entry_node = $data->{entry};
				if (defined($entry_node)) {
					my $name_entry = $entry_node->{name};
					$entry_Hash{'name'}=$name_entry;
					my $prot = $entry_node->{protein};
					if(defined($prot)){
						my $recName = $prot->{recommendedName};
						if (defined($recName)){
							my $fullName = $recName->{fullName};
							if (defined($fullName)){
								if (ref $fullName eq ref {}){
									my $nameValue = $fullName->{content};
									if (defined($nameValue)){
										$entry_Hash{'fullName'} = $nameValue;
									}
									else{
										print "The fullName tag has been placed but its content is undefined";
									}
								}
								else{
									$entry_Hash{'fullName'} = $fullName;
								}
							}
							else{
								print "XML document contains no fullName node under recommendedName";
							}
						}
						else{
							print "XML protein node contains no recommendedName node";
						}
					}
					else{
						print "XML document contains no protein node";
					}
					my $seq = $entry_node->{sequence};
					if(defined($seq)){
						my $seqCode = $seq->{content};
						$entry_Hash{'Seq'}=$seqCode;
					}
					else{
						print "No entry contains no sequence node";
					}
				}
				else{
					print "XML document does not contain entry node";
				}
			#Make the value of the key (protein id) in the final_Hash, be a reference to the inner Hash.
			#The inner Hash gets overridden during the loop, but its data is stored in the final_Hash.
			$final_Hash{$prot_id} = \%entry_Hash;
			print "$prot_id content is processed successfully\n";
		}
		else{
			print "Content type is not XML";
		}
	}
	else{
		print "Protein ID follows correct format, but URL is broken";
	}
	#last; inserted for troubleshooting
}

#Now we unpack the final_Hash, this can be done with 1 loop since we know the name of each inner key.
while (my ($key, $value) = each(%final_Hash)){
	open(my $oh, '>:encoding(UTF-8)', "./Resources/$key.fasta"); #create, open, write, and close files inside this loop.
	my $fullname = $value->{'fullName'};
	my $name = $value->{'name'};
	my $sequence = $value->{'Seq'};
	$sequence =~ s/(.{1,80})/$1\n/gs;
	print {$oh} ">".$key."|".$name."|".$fullname."\n".$sequence."\n";
	close $oh;
}
close $fh; #close the prot_id file.
