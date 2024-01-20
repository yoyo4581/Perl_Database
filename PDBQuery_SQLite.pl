use warnings;
use strict;

use LWP::Simple;
use XML::Simple qw(:strict);
use Data::Dumper;
use DBI;


my $input = <STDIN>;
$input =~ s/\R//g;;



my $dbfile = "database1.db";
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile");

my $query = "SELECT PDBID FROM ids WHERE ids.PDBID = ?";
my $check_name = $dbh->prepare($query);
my $result = $check_name->execute($input);

#I have to do the check using this method, because $result always returns a true value. doing fetchrow_array, checks if that value is empty or not.
#check if the value is in table 2
my $truth_st = 1;
while (my @row = $check_name->fetchrow_array){
	if ($truth_st){
		$truth_st = 0;
	}
	print "PDBID $input is in the table ids"."\n";
	my $query2 = "SELECT Names.name, ids.UniProtId, GOTerms.GOID, GOTerms.term\
	 FROM ids, Names, GOTerms WHERE ids.PDBID = ? AND ids.UniProtId = Names.UniProtId AND ids.UniProtId=GOTerms.UniProtId";
	my $check_name2 = $dbh->prepare($query2);
	$check_name2->execute($input);
	while (my @row = $check_name2->fetchrow_array){
		print $row[0]." ".$row[1]." ".$row[2]." ".$row[3]."\n";
	}
	$check_name2->finish();

}
#if it isn't in table 2, this statement will occur and the while loop will be skipped
if($truth_st){
	print "PDBID $input is not in the table ids"."\n";
}



$check_name->finish();
$dbh->disconnect();
