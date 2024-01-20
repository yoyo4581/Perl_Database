#Yahya Al Sabeh 
use strict;
use warnings;

use LWP::Simple;
use XML::Simple qw(:strict);
use Data::Dumper;
use DBI;


my $browser = LWP::UserAgent->new;

my $filename = "./Resources/UniProt2_2.txt";
my $dbfile = "database1.db";
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile");

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

#Parsing occurs in this loop. Database creation and datavalue insertion occurs below it.
foreach (@ids){
	print $_."\n";
	#URL differs based on each element in the @ids
	my $url = "https://www.uniprot.org/uniprot/$_.xml";
#-----------------------------------------------------------------------------------------------------------------------------#
							#Strategy
	#set every element in our @ids array to a variable prot_id, make this an undefined key in our final Hash.
	#The final Hash will be a key (prot_id) and a hash reference as value pair. The hash reference will include a hash that contains all information related to that prot_id
	#The hash reference (entry_Hash) is composed of keys that correspond to the data types that we want. For names, scientific names, and organism, they are found in standard
	#key-value pairs, because there is one value for each of these data types relating to a UniProtId. 
	#For X-ray PDBs (pdbIds), these are stored as array references, because more than one data value can exist and the order of the PDBs doesn't matter.
	#As for the GO References, they are stored as a hash reference of GO_Ref, this is because each GOid has a related GOTerm, and these pieces of information are linked, so they
	#will be stored as key-value pairs.
	my $prot_id = $_;  
	$final_Hash{$prot_id} = undef;
	
	my $response = $browser->get($url, 'User-Agent' => 'Mozilla/4.0 (compatible; MSIE 7.0)');
	if ($response->is_success) {
		# We got something.
		print 'Content type is ', $response->content_type, "\n";
		if ($response->content_type eq "application/xml") {
			#entry_Hash will be created once a valid xml has been found, this is the Hash reference linked to a key in final_Hash
			my %entry_Hash;		#create inner data structures, we can do checks on if these datastructures are populated and print errors.
			my @xray_Ref = ();
			my %GO_Ref = {};
			print "Process an XML response\n";
			my $xml = new XML::Simple();
			#Prevent duplicate keys from overriding each other by forcing into array
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
								#fullName data structure differs
								#if the fullName data type is a hash, then parse it this way
								if (ref $fullName eq ref {}){	
									my $nameValue = $fullName->{content};
									if (defined($nameValue)){
										$entry_Hash{'fullName'} = $nameValue;
									}
									else{
										print "The fullName tag has been placed but its content is undefined";
									}
								}
								else{	#since its not a hash, simply insert it into entry_Hash as a value
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
					my $org = $entry_node->{organism};
					if(defined($org)){
						my $org_name = $org->{name};
						if(defined($org_name)){
							foreach ($org_name){
								#check the datatype of the org_name node, sometimes its array of hashes, sometimes its hashes
								if (ref $_ eq 'ARRAY'){	 
									foreach my $element(@$_){
										if (%$element{type} eq 'scientific'){
											$entry_Hash{'scientific'} = %$element{content};
											print %$element{content}."\n";
										}
									}	
								}
								elsif (ref $_ eq {}){
									if (%$_{type} eq 'scientific'){
										$entry_Hash{'scientific'} = %$_{content};
										print %$_{content}."\n";
									}
								}
								else{
									print "organism subnodes are neither array of hashes nor hashes";
								}							
							}
						}
						else{
							print "Entry contains no organism name node";
						}
					}
					else{
						print "Entry contains no organism node";
					}
					# Know dbReference is an array of hashes
					my $dbref = $entry_node->{dbReference};
					if (defined($dbref)) {
						#datatype if ref is array of Hashes:
						foreach my $ref (@$dbref){		 
							#each element has hash keys (id, type, property), 
							#property is an array of Hashes each with a key-value tuplet. [[Hash],[Hash]]. In this tuplet, the keys are term, and value.
							my $idVal = $ref->{id}; 	
							my $idType = $ref->{type};
							#As we iterate through the array of hashes, we note hash value, if hash value of key "type" is GO we access it
							if ($idType eq 'GO'){	
								#Now that we arrived at dbref entries with GO dataType, we look at the values of the property keys
								my $idprop = $ref->{property};
								#Iterate through property array	
								foreach my $propelem (@$idprop){
									#Iterate through each key-value tuplets.	
									while (my ($propkey, $propval) = each(%$propelem)){
										#Find one of the values in the key-value tuplet, with a value of 'term'	
										if ($propval eq 'term'){
											#link back to the Hash and get the term from that property by using the value key	
											my $termVal = %$propelem{value};
											#link back to the dbref element and get its id. Then add to the inner GO_Ref hash {Goid:term}	
											$GO_Ref{$idVal} = $termVal;		
										}
									}
								}
							}
							if ($idType eq 'PDB'){
								my $idprop = $ref->{property};	
								foreach my $propelem (@$idprop){
									#Traverse through array of key-val tuplets, to find the one with X-ray method, Similar to top
									while (my ($propkey, $propval) = each(%$propelem)){
										if ($propval eq 'X-ray'){
											#Link back to the ref datatype, get the value of the hash with id key.
											my $idVal = $ref->{id};	
											#add it to the list xray_Ref	
											push(@xray_Ref, $idVal);
										}
									}
								}
										
							}
						}
						#if xray_Ref array or GO_Ref hash are empty, say that the XML doesn't have each of the types of data
						if (!@xray_Ref){			
							print "$prot_id XML document does not contain X-rays"."\n";
							push(@xray_Ref, "None");
						}
						if (!%GO_Ref){
							print "$prot_id XML document does not contain GO-terms"."\n";
							$GO_Ref{"None"} = "None";
						}
					 }
					 else{
					 	print "XML document does not contain a dbreference node";
					 }	 
				}
				else{
					print "XML document does not contain entry node";
				}
			#final_Hash{prot_id} = innerHash reference.
			#InnerHash reference, has keys-values of: 
			#'X-ray'-->Array of PDBids, 
			#'GO'-->Hash (Key:Term id, Value:Term Val),
			#(key-value pairs): 
				#fullname, 
				#name, 
				#orgname
			$entry_Hash{'X-ray'} = \@xray_Ref;
			$entry_Hash{'GO'} = \%GO_Ref;		
			$final_Hash{$prot_id} = \%entry_Hash;
		}
		else{
			print "Content type is not XML";
		}
	}
	else{
		print "Protein ID follows correct format, but URL is broken";
	}
	#last; for debugging

}

#Check if the table Names exists
my $check_name = $dbh->selectall_arrayref("SELECT name FROM sqlite_master WHERE type='table' AND name='Names'");
#If the table Names doesn't exist then create it.
if (!@$check_name){
	$dbh->do("create table Names (UniProtId, name, recommendedName, organism)") or die $DBI::errstr;
	print("Table Names has been created!"."\n");
}

#Do the same for the other tables
my $check_ids = $dbh->selectall_arrayref("SELECT name FROM sqlite_master WHERE type='table' AND name='ids'");
if (!@$check_ids){
	$dbh->do("create table ids (UniProtId, PDBID)") or die $DBI::errstr;
	print("Table ids has been created!"."\n");
}
my $check_terms = $dbh->selectall_arrayref("SELECT name FROM sqlite_master WHERE type='table' AND name='GOTerms'");
if (!@$check_terms){
	$dbh->do("create table GOTerms (UniProtId, GOID, term)") or die $DBI::errstr;
	print("Table GOTerms has been created!"."\n");
}


#Unpack finalHash and insert into table
while (my ($key, $value) = each(%final_Hash)){

	my $fullname = $value->{'fullName'};
	my $name = $value->{'name'};
	my $orgName = $value->{'scientific'};
	my $pdbIds = $value->{'X-ray'};
	my $go_ids = $value->{'GO'};
	

	$dbh->do("insert into Names values ('$key','$name','$fullname','$orgName')") or die $DBI::errstr;
	print("Table Names inserted $key, $name, $fullname, $orgName"."\n");
	#unpack pdbIds (Array), and go_ids (hash)
	foreach my $PDBid (@$pdbIds){
		$dbh->do("insert into ids values ('$key','$PDBid')") or die $DBI::errstr;
	}
	print("Table ids inserted PDBs for $key"."\n");	
	
	while (my($goId, $goTerm)  = each(%$go_ids)){
		$dbh->do("insert into GOTerms values ('$key','$goId', '$goTerm')") or die $DBI::errstr;
	}
	print("Table GOTerms inserted GOTerms for $key"."\n");		

}

#disconnect from the database.
$dbh->disconnect;
#close the prot_id file.	
close $fh; 


#16.
#The way the current script is set up, everytime I rerun the script, it will add values to the current table, basically doing another parse and addition to the current table in the database.
#We need to do a check on the database, preferably, if the current database table already has a UniProtId value that is currently in it, if such a UniProtId value already exists,
#then skip the addition of this entry. It's best to do this before the parsing loop to avoid excessive computation, we can do this with 3 SQL statements and maybe using the selectall_arrayref
#function.
